"""
Resume Screener
==================================================
A full-stack, modular web application demonstrating:
- Dual Role Registration & Portals: Recruiter & Candidate
- Domain 1: Machine Learning (TF-IDF & Cosine Similarity)
- Domain 2: Full Stack Development (Flask, SQLite, HTML5, CSS3, JS, Chart.js)
- Domain 3: Software Engineering (Modular design, Clean RESTful routes, Validation)
- Domain 4: Operating Systems (Producer-Consumer queue, Background Worker Thread)

Running on: http://127.0.0.1:5001
"""

import os
import re
import queue
import threading
import sqlite3
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g, jsonify
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Import ML and Parsing Modules
from ml.ranking import evaluate_candidate_for_job, extract_skill_comparison
from utils.resume_parser import parse_resume

# Initialize Flask Application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'resume_screener_secret_key_2026'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'resumes')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload limit
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# Ensure uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==============================================================================
# DOMAIN 4: OPERATING SYSTEMS - ASYNCHRONOUS WORKER QUEUE (Producer-Consumer)
# ==============================================================================
resume_queue = queue.Queue()

def get_thread_db():
    """Returns a standalone SQLite connection safe for background worker threads."""
    conn = sqlite3.connect(DATABASE_FILE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def resume_processing_worker():
    """
    Background worker thread function (Consumer).
    Continuously dequeues tasks, executes text extraction & TF-IDF similarity,
    and commits candidate evaluations into SQLite.
    """
    print("[OS Thread] Background Resume Processing Worker Started.")
    while True:
        try:
            # Blocking wait for task
            task = resume_queue.get()
            if task is None:
                break

            # Handle 3-tuple or 4-tuple tasks
            if len(task) == 4:
                filepath, filename, job_id, user_id = task
            else:
                filepath, filename, job_id = task
                user_id = None

            print(f"[OS Queue] Consumer picked up: {filename} for Job #{job_id}")

            conn = get_thread_db()
            cursor = conn.cursor()

            # Retrieve job requirements for NLP matching
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            job_row = cursor.fetchone()

            if not job_row:
                print(f"[OS Worker Error] Job #{job_id} not found in database.")
                resume_queue.task_done()
                conn.close()
                continue

            job = dict(job_row)

            # Step 1: Parse resume file (PDF or DOCX)
            parsed_data = parse_resume(filepath)

            # If user_id is provided, try to fetch candidate user's name/email if not in parsed text
            candidate_name = parsed_data['name']
            candidate_email = parsed_data['email']
            if user_id:
                cursor.execute("SELECT name, email FROM users WHERE id = ?", (user_id,))
                user_row = cursor.fetchone()
                if user_row:
                    if candidate_name == "Candidate":
                        candidate_name = user_row['name']
                    if candidate_email == "Not provided":
                        candidate_email = user_row['email']

            # Step 2: Machine Learning - TF-IDF Vectorization & Cosine Similarity
            match_score = evaluate_candidate_for_job(job, parsed_data)
            print(f"[ML Engine] Match Score for '{candidate_name}' on '{job['title']}': {match_score}%")

            # Step 3: Insert candidate record into SQLite
            cursor.execute("""
                INSERT INTO candidates (
                    user_id, name, email, phone, resume_filename, resume_text,
                    skills, education, experience, match_score, status, job_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
            """, (
                user_id,
                candidate_name,
                candidate_email,
                parsed_data['phone'],
                filename,
                parsed_data['raw_text'],
                parsed_data['skills'],
                parsed_data['education'],
                parsed_data['experience'],
                match_score,
                job_id
            ))
            conn.commit()
            conn.close()
            print(f"[OS Worker Success] Candidate '{candidate_name}' successfully processed and saved!")

            resume_queue.task_done()

        except Exception as e:
            print(f"[OS Worker Exception] Error processing resume task: {e}")
            try:
                resume_queue.task_done()
            except Exception:
                pass

# Start background worker daemon thread
worker_thread = threading.Thread(target=resume_processing_worker, daemon=True)
worker_thread.start()


# ==============================================================================
# DATABASE INITIALIZATION (SQLite)
# ==============================================================================
def init_db():
    """Initializes SQLite database tables."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")

    # 1. Users Table (Supports both Recruiter and Candidate)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'recruiter',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Jobs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            skills TEXT NOT NULL,
            education TEXT,
            experience TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 3. Candidates Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            email TEXT,
            phone TEXT,
            resume_filename TEXT,
            resume_text TEXT,
            skills TEXT,
            education TEXT,
            experience TEXT,
            match_score REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Pending',
            job_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
    """)

    # Safely migrate existing table to include user_id if needed
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN user_id INTEGER;")
    except Exception:
        pass

    # 4. Interviews Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            interview_type TEXT NOT NULL,
            meeting_link TEXT,
            status TEXT DEFAULT 'Scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()
    print("[Database] SQLite database initialized at:", DATABASE_FILE)

def get_db():
    """Per-request database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_FILE, timeout=30.0)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ==============================================================================
# AUTHENTICATION & ACCESS CONTROL HELPERS
# ==============================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def recruiter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in as a recruiter.", "warning")
            return redirect(url_for('login'))
        if session.get('role') != 'recruiter':
            flash("Access restricted to recruiters.", "error")
            return redirect(url_for('candidate_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def candidate_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in as a candidate.", "warning")
            return redirect(url_for('login'))
        if session.get('role') != 'candidate':
            flash("Only candidates can apply for jobs.", "error")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==============================================================================
# PUBLIC ROUTES
# ==============================================================================
@app.route('/')
def index():
    """Landing Page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Dual Role Registration: Recruiter & Candidate"""
    selected_role = request.args.get('role', 'recruiter')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'recruiter').lower()

        if role not in ['recruiter', 'candidate']:
            role = 'recruiter'

        # Validations
        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "error")
            return render_template('register.html', selected_role=role)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('register.html', selected_role=role)

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template('register.html', selected_role=role)

        # Unique email check
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            flash("This email is already registered. Please sign in.", "error")
            return render_template('register.html', selected_role=role)

        # Werkzeug Password Hashing
        hashed_password = generate_password_hash(password)

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, hashed_password, role)
            )
            db.commit()
            flash(f"Account created successfully as {role.capitalize()}! Please sign in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration error: {e}", "error")
            return render_template('register.html', selected_role=role)

    return render_template('register.html', selected_role=selected_role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login for both Recruiters and Candidates with automatic role routing"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please provide both email and password.", "error")
            return render_template('login.html')

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = user['role']
            flash(f"Welcome back, {user['name']}!", "success")

            # Route based on role
            if user['role'] == 'candidate':
                return redirect(url_for('candidate_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('login'))


# ==============================================================================
# CANDIDATE PORTAL ROUTES
# ==============================================================================
@app.route('/candidate/dashboard')
@login_required
def candidate_dashboard():
    """Candidate Personal Dashboard"""
    db = get_db()
    cursor = db.cursor()

    user_id = session['user_id']
    user_email = session['user_email']

    # Retrieve all candidate applications submitted by this user
    cursor.execute("""
        SELECT c.*, j.title AS job_title, j.skills AS job_skills
        FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE c.user_id = ? OR c.email = ?
        ORDER BY c.created_at DESC
    """, (user_id, user_email))
    applications = [dict(row) for row in cursor.fetchall()]

    # Stats
    top_score = max([app['match_score'] for app in applications], default=0.0)
    shortlisted_count = sum(1 for app in applications if app['status'] == 'Shortlisted')

    # Retrieve scheduled interviews
    cursor.execute("""
        SELECT i.*, j.title AS job_title
        FROM interviews i
        JOIN candidates c ON i.candidate_id = c.id
        JOIN jobs j ON c.job_id = j.id
        WHERE (c.user_id = ? OR c.email = ?) AND i.status = 'Scheduled'
        ORDER BY i.date ASC, i.time ASC
    """, (user_id, user_email))
    interviews = [dict(row) for row in cursor.fetchall()]

    return render_template(
        'candidate_dashboard.html',
        applications=applications,
        top_score=top_score,
        shortlisted_count=shortlisted_count,
        interviews=interviews
    )

@app.route('/candidate/jobs')
@candidate_required
def candidate_jobs():
    """Candidate: Browse open jobs to apply"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT j.*
        FROM jobs j
        WHERE j.id = (
            SELECT MAX(j2.id)
            FROM jobs j2
            WHERE j2.title = j.title COLLATE NOCASE
        )
        ORDER BY j.created_at DESC, j.id DESC
    """)
    jobs = [dict(row) for row in cursor.fetchall()]
    return render_template('candidate_jobs.html', jobs=jobs)

@app.route('/candidate/apply/<int:job_id>', methods=['POST'])
@candidate_required
def candidate_apply(job_id):
    """Candidate: Upload resume and apply to a job"""
    if 'resume_file' not in request.files:
        flash("No file uploaded.", "error")
        return redirect(url_for('candidate_jobs'))

    file = request.files['resume_file']
    if file.filename == '' or not allowed_file(file.filename):
        flash("Please upload a valid PDF or Word document (.docx).", "error")
        return redirect(url_for('candidate_jobs'))

    original_name = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_filename = f"{timestamp}_{original_name}"
    saved_filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
    file.save(saved_filepath)

    # Enqueue task for background OS worker
    task = (saved_filepath, saved_filename, int(job_id), session['user_id'])
    resume_queue.put(task)
    print(f"[OS Queue] Candidate '{session['user_name']}' enqueued resume: {saved_filename}")

    flash(
        f"Resume '{original_name}' submitted successfully! Our background NLP screening engine is matching it now.",
        "success"
    )
    return redirect(url_for('candidate_dashboard'))

@app.route('/candidate/application/<int:application_id>/delete', methods=['POST'])
@candidate_required
def delete_candidate_application(application_id):
    """Let a candidate withdraw one of their own applications."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT resume_filename FROM candidates WHERE id = ? AND user_id = ?",
        (application_id, session['user_id'])
    )
    application = cursor.fetchone()

    if not application:
        flash("Application not found or you do not have permission to delete it.", "error")
        return redirect(url_for('candidate_dashboard'))

    resume_filename = application['resume_filename']
    cursor.execute(
        "DELETE FROM candidates WHERE id = ? AND user_id = ?",
        (application_id, session['user_id'])
    )
    db.commit()

    if resume_filename:
        upload_folder = os.path.realpath(app.config['UPLOAD_FOLDER'])
        resume_path = os.path.realpath(os.path.join(upload_folder, resume_filename))
        if os.path.commonpath([upload_folder, resume_path]) != upload_folder:
            app.logger.error("Refusing to delete resume outside upload folder: %s", resume_filename)
            flash("Application deleted, but its resume file could not be safely removed.", "error")
            return redirect(url_for('candidate_dashboard'))
        try:
            if os.path.isfile(resume_path):
                os.remove(resume_path)
        except OSError:
            app.logger.exception("Failed to remove resume file for application %s", application_id)
            flash("Application deleted, but the resume file could not be removed.", "error")
            return redirect(url_for('candidate_dashboard'))

    flash("Your job application and its uploaded resume have been deleted.", "success")
    return redirect(url_for('candidate_dashboard'))

@app.route('/candidate/my-interviews')
@login_required
def candidate_my_interviews():
    """Candidate: View scheduled interviews"""
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    user_email = session['user_email']

    cursor.execute("""
        SELECT i.*, j.title AS job_title
        FROM interviews i
        JOIN candidates c ON i.candidate_id = c.id
        JOIN jobs j ON c.job_id = j.id
        WHERE c.user_id = ? OR c.email = ?
        ORDER BY i.date ASC, i.time ASC
    """, (user_id, user_email))
    interview_list = [dict(row) for row in cursor.fetchall()]

    return render_template('candidate_interviews.html', interviews=interview_list)


# ==============================================================================
# RECRUITER PORTAL ROUTES
# ==============================================================================
@app.route('/dashboard')
@recruiter_required
def dashboard():
    """Recruiter Dashboard with live SQLite aggregations"""
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']

    # Dynamic metrics from SQLite
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE created_by = ?", (user_id,))
    total_jobs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE j.created_by = ?
    """, (user_id,))
    total_candidates = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE j.created_by = ? AND c.status = 'Shortlisted'
    """, (user_id,))
    shortlisted = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE j.created_by = ? AND c.status = 'Rejected'
    """, (user_id,))
    rejected = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM interviews i
        JOIN candidates c ON i.candidate_id = c.id
        JOIN jobs j ON c.job_id = j.id
        WHERE j.created_by = ? AND i.status = 'Scheduled'
    """, (user_id,))
    upcoming_interviews = cursor.fetchone()[0]

    stats = {
        'total_jobs': total_jobs,
        'total_candidates': total_candidates,
        'shortlisted': shortlisted,
        'rejected': rejected,
        'upcoming_interviews': upcoming_interviews
    }

    cursor.execute("""
        SELECT c.*, j.title AS job_title
        FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE j.created_by = ?
        ORDER BY c.match_score DESC
        LIMIT 5
    """, (user_id,))
    top_candidates = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT j.*, (SELECT COUNT(*) FROM candidates WHERE job_id = j.id) AS candidate_count
        FROM jobs j
        WHERE j.created_by = ?
        ORDER BY j.created_at DESC
        LIMIT 4
    """, (user_id,))
    recent_jobs = [dict(row) for row in cursor.fetchall()]

    return render_template('dashboard.html', stats=stats, top_candidates=top_candidates, recent_jobs=recent_jobs)


# ==============================================================================
# JOB MANAGEMENT (CRUD)
# ==============================================================================
@app.route('/jobs')
@recruiter_required
def jobs():
    """List all jobs posted by this recruiter"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT j.*, (SELECT COUNT(*) FROM candidates WHERE job_id = j.id) AS candidate_count
        FROM jobs j
        WHERE j.created_by = ?
        ORDER BY j.created_at DESC
    """, (session['user_id'],))
    job_list = [dict(row) for row in cursor.fetchall()]
    return render_template('jobs.html', jobs=job_list)

@app.route('/jobs/create', methods=['GET', 'POST'])
@recruiter_required
def create_job():
    """Create a new job opening"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills', '').strip()
        education = request.form.get('education', '').strip()
        experience = request.form.get('experience', '').strip()

        if not title or not description or not skills:
            flash("Job title, description, and required skills are required.", "error")
            return render_template('create_job.html')

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO jobs (title, description, skills, education, experience, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, description, skills, education, experience, session['user_id']))
        db.commit()
        new_job_id = cursor.lastrowid
        flash(f"Job opening '{title}' created successfully!", "success")
        return redirect(url_for('job_details', id=new_job_id))

    return render_template('create_job.html')

@app.route('/jobs/<int:id>')
@recruiter_required
def job_details(id):
    """View job details and ranked candidates"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ? AND created_by = ?", (id, session['user_id']))
    job = cursor.fetchone()

    if not job:
        flash("Job not found or access denied.", "error")
        return redirect(url_for('jobs'))

    cursor.execute("""
        SELECT * FROM candidates
        WHERE job_id = ?
        ORDER BY match_score DESC
    """, (id,))
    candidates = [dict(row) for row in cursor.fetchall()]

    return render_template('job_details.html', job=dict(job), candidates=candidates)

@app.route('/jobs/<int:id>/edit', methods=['GET', 'POST'])
@recruiter_required
def edit_job(id):
    """Edit existing job"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ? AND created_by = ?", (id, session['user_id']))
    job = cursor.fetchone()

    if not job:
        flash("Job not found.", "error")
        return redirect(url_for('jobs'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills', '').strip()
        education = request.form.get('education', '').strip()
        experience = request.form.get('experience', '').strip()

        if not title or not description or not skills:
            flash("Title, description, and skills cannot be empty.", "error")
            return render_template('edit_job.html', job=dict(job))

        cursor.execute("""
            UPDATE jobs
            SET title = ?, description = ?, skills = ?, education = ?, experience = ?
            WHERE id = ? AND created_by = ?
        """, (title, description, skills, education, experience, id, session['user_id']))
        db.commit()
        flash("Job details updated successfully.", "success")
        return redirect(url_for('job_details', id=id))

    return render_template('edit_job.html', job=dict(job))

@app.route('/jobs/<int:id>/delete', methods=['POST'])
@recruiter_required
def delete_job(id):
    """Delete a job and linked candidates"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM jobs WHERE id = ? AND created_by = ?", (id, session['user_id']))
    job = cursor.fetchone()

    if not job:
        flash("Job not found.", "error")
        return redirect(url_for('jobs'))

    cursor.execute("DELETE FROM jobs WHERE id = ?", (id,))
    db.commit()
    flash("Job opening deleted successfully.", "info")
    return redirect(url_for('jobs'))


# ==============================================================================
# RECRUITER RESUME UPLOAD (OS QUEUE)
# ==============================================================================
@app.route('/upload', methods=['GET', 'POST'])
@recruiter_required
def retired_resume_upload():
    """Keep old recruiter upload links from bypassing candidate applications."""
    flash("Candidates must apply for jobs and submit their own resumes.", "info")
    return redirect(url_for('candidates'))

# ==============================================================================
# CANDIDATE MANAGEMENT & RANKING
# ==============================================================================
@app.route('/candidates')
@recruiter_required
def candidates():
    """View candidate leaderboard ranked by match score DESC"""
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']
    selected_job_id = request.args.get('job_id', '')

    cursor.execute("SELECT id, title FROM jobs WHERE created_by = ? ORDER BY title ASC", (user_id,))
    jobs = [dict(row) for row in cursor.fetchall()]

    if selected_job_id:
        cursor.execute("""
            SELECT c.*, j.title AS job_title
            FROM candidates c
            JOIN jobs j ON c.job_id = j.id
            WHERE j.created_by = ? AND j.id = ?
            ORDER BY c.match_score DESC
        """, (user_id, selected_job_id))
    else:
        cursor.execute("""
            SELECT c.*, j.title AS job_title
            FROM candidates c
            JOIN jobs j ON c.job_id = j.id
            WHERE j.created_by = ?
            ORDER BY c.match_score DESC
        """, (user_id,))

    candidate_list = [dict(row) for row in cursor.fetchall()]
    return render_template('candidates.html', candidates=candidate_list, jobs=jobs, selected_job_id=selected_job_id)

@app.route('/candidate/<int:id>')
@recruiter_required
def candidate_details(id):
    """View candidate details, skill gap analysis, and match breakdown"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT c.*, j.title AS job_title, j.skills AS job_skills
        FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE c.id = ? AND j.created_by = ?
    """, (id, session['user_id']))
    cand_row = cursor.fetchone()

    if not cand_row:
        flash("Candidate not found or access denied.", "error")
        return redirect(url_for('candidates'))

    candidate = dict(cand_row)

    matched_skills, missing_skills = extract_skill_comparison(
        candidate.get('job_skills', ''),
        candidate.get('skills', '')
    )

    cursor.execute("SELECT * FROM interviews WHERE candidate_id = ? ORDER BY date DESC, time DESC", (id,))
    interviews = [dict(row) for row in cursor.fetchall()]

    return render_template(
        'candidate_details.html',
        candidate=candidate,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        interviews=interviews
    )

@app.route('/candidate/<int:id>/shortlist')
@recruiter_required
def shortlist_candidate(id):
    """Shortlist a candidate"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE candidates
        SET status = 'Shortlisted'
        WHERE id = ? AND job_id IN (SELECT id FROM jobs WHERE created_by = ?)
    """, (id, session['user_id']))
    db.commit()
    flash("Candidate successfully shortlisted!", "success")
    return redirect(request.referrer or url_for('candidates'))

@app.route('/candidate/<int:id>/reject')
@recruiter_required
def reject_candidate(id):
    """Reject a candidate"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE candidates
        SET status = 'Rejected'
        WHERE id = ? AND job_id IN (SELECT id FROM jobs WHERE created_by = ?)
    """, (id, session['user_id']))
    db.commit()
    flash("Candidate marked as rejected.", "info")
    return redirect(request.referrer or url_for('candidates'))


# ==============================================================================
# INTERVIEWS SCHEDULING & MANAGEMENT
# ==============================================================================
@app.route('/candidate/<int:id>/schedule', methods=['GET', 'POST'])
@recruiter_required
def schedule_interview(id):
    """Schedule interview for candidate"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT c.*, j.title AS job_title
        FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE c.id = ? AND j.created_by = ?
    """, (id, session['user_id']))
    cand_row = cursor.fetchone()

    if not cand_row:
        flash("Candidate not found.", "error")
        return redirect(url_for('candidates'))

    candidate = dict(cand_row)

    if request.method == 'POST':
        date = request.form.get('date', '').strip()
        time = request.form.get('time', '').strip()
        interview_type = request.form.get('interview_type', 'Online')
        meeting_link = request.form.get('meeting_link', '').strip()

        if not date or not time:
            flash("Date and Time are required.", "error")
            return render_template('schedule.html', candidate=candidate)

        cursor.execute("""
            INSERT INTO interviews (candidate_id, date, time, interview_type, meeting_link, status)
            VALUES (?, ?, ?, ?, ?, 'Scheduled')
        """, (id, date, time, interview_type, meeting_link))

        cursor.execute("UPDATE candidates SET status = 'Interview Scheduled' WHERE id = ?", (id,))
        db.commit()

        flash(f"Interview scheduled with {candidate['name']} on {date} at {time}.", "success")
        return redirect(url_for('interviews'))

    return render_template('schedule.html', candidate=candidate)

@app.route('/interviews')
@recruiter_required
def interviews():
    """List all scheduled interviews"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT i.*, c.name AS candidate_name, c.email AS candidate_email, j.title AS job_title
        FROM interviews i
        JOIN candidates c ON i.candidate_id = c.id
        JOIN jobs j ON c.job_id = j.id
        WHERE j.created_by = ?
        ORDER BY i.date ASC, i.time ASC
    """, (session['user_id'],))
    interview_list = [dict(row) for row in cursor.fetchall()]

    return render_template('interviews.html', interviews=interview_list)

@app.route('/interview/<int:id>/complete')
@recruiter_required
def complete_interview(id):
    """Mark interview as Completed"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE interviews
        SET status = 'Completed'
        WHERE id = ? AND candidate_id IN (
            SELECT c.id FROM candidates c
            JOIN jobs j ON c.job_id = j.id
            WHERE j.created_by = ?
        )
    """, (id, session['user_id']))
    db.commit()
    flash("Interview marked as Completed.", "success")
    return redirect(url_for('interviews'))

@app.route('/interview/<int:id>/cancel')
@recruiter_required
def cancel_interview(id):
    """Mark interview as Cancelled"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE interviews
        SET status = 'Cancelled'
        WHERE id = ? AND candidate_id IN (
            SELECT c.id FROM candidates c
            JOIN jobs j ON c.job_id = j.id
            WHERE j.created_by = ?
        )
    """, (id, session['user_id']))
    db.commit()
    flash("Interview cancelled.", "info")
    return redirect(url_for('interviews'))


# ==============================================================================
# ANALYTICS DASHBOARD
# ==============================================================================
@app.route('/analytics')
@recruiter_required
def analytics():
    """Analytics dashboard with live SQL aggregations"""
    db = get_db()
    cursor = db.cursor()
    user_id = session['user_id']

    cursor.execute("SELECT COUNT(*) FROM jobs WHERE created_by = ?", (user_id,))
    total_jobs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE j.created_by = ?
    """, (user_id,))
    total_candidates = cursor.fetchone()[0]

    cursor.execute("""
        SELECT status, COUNT(*) FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE j.created_by = ?
        GROUP BY status
    """, (user_id,))
    status_counts = dict(cursor.fetchall())

    shortlisted = status_counts.get('Shortlisted', 0)
    rejected = status_counts.get('Rejected', 0)
    pending = status_counts.get('Pending', 0)
    interviews_scheduled = status_counts.get('Interview Scheduled', 0)

    stats = {
        'total_jobs': total_jobs,
        'total_candidates': total_candidates,
        'shortlisted': shortlisted,
        'rejected': rejected,
        'pending': pending,
        'interviews_scheduled': interviews_scheduled
    }

    cursor.execute("""
        SELECT match_score FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE j.created_by = ?
    """, (user_id,))
    scores = [row[0] for row in cursor.fetchall()]

    score_buckets = {
        '0_20': sum(1 for s in scores if 0 <= s <= 20),
        '21_40': sum(1 for s in scores if 20 < s <= 40),
        '41_60': sum(1 for s in scores if 40 < s <= 60),
        '61_80': sum(1 for s in scores if 60 < s <= 80),
        '81_100': sum(1 for s in scores if 80 < s <= 100),
    }

    cursor.execute("""
        SELECT j.title, COUNT(c.id) AS count
        FROM jobs j
        LEFT JOIN candidates c ON j.id = c.job_id
        WHERE j.created_by = ?
        GROUP BY j.id
        ORDER BY count DESC
        LIMIT 10
    """, (user_id,))
    job_dist_rows = cursor.fetchall()
    jobs_distribution = {
        'labels': [row[0] for row in job_dist_rows],
        'counts': [row[1] for row in job_dist_rows]
    }

    return render_template(
        'analytics.html',
        stats=stats,
        score_buckets=score_buckets,
        jobs_distribution=jobs_distribution
    )


# ==============================================================================
# MAIN APPLICATION ENTRY POINT (Port 5001)
# ==============================================================================
if __name__ == '__main__':
    init_db()

    print("\n=======================================================")
    print("  Resume Screener")
    print("  Recruiter & Candidate Portals Active")
    print("  Localhost URL: http://127.0.0.1:5001")
    print("=======================================================\n")

    app.run(debug=True, host='127.0.0.1', port=5001)
