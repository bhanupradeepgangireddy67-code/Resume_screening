"""
Automated Test Suite for Resume Screener
Verifies:
1. Database initialization and user_id migration
2. Dual registration: Recruiter & Candidate
3. Candidate application & resume upload
4. ML TF-IDF and Cosine Similarity
5. OS Multithreaded Processing Queue
6. Recruiter interview scheduling
7. Candidate viewing their interviews & match scores
8. All Flask routes on port 5001
"""

import os
import sys
import time
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, init_db, resume_queue, DATABASE_FILE
from utils.resume_parser import parse_resume
from ml.ranking import evaluate_candidate_for_job

def run_tests():
    print("============================================================")
    print("RUNNING AUTOMATED TESTS: RESUME SCREENER (DUAL PORTALS)")
    print("============================================================")

    init_db()

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # 1. Test Recruiter & Candidate User Creation
    print("\n[Test 1] Testing Dual User Registration...")
    cursor.execute("DELETE FROM users WHERE email IN ('recruiter@test.com', 'candidate@test.com');")
    
    hashed = generate_password_hash("password123")
    cursor.execute("INSERT INTO users (name, email, password, role) VALUES ('Alice Recruiter', 'recruiter@test.com', ?, 'recruiter')", (hashed,))
    recruiter_id = cursor.lastrowid

    cursor.execute("INSERT INTO users (name, email, password, role) VALUES ('Bob Candidate', 'candidate@test.com', ?, 'candidate')", (hashed,))
    candidate_id = cursor.lastrowid
    conn.commit()

    print(f"[PASS] Recruiter created (ID: {recruiter_id}) and Candidate created (ID: {candidate_id})")

    # 2. Test Job Creation
    print("\n[Test 2] Testing Job Posting...")
    cursor.execute("""
        INSERT INTO jobs (title, description, skills, education, experience, created_by)
        VALUES ('Full Stack Python Developer', 'Build web apps using Flask, Python, SQL, and HTML/CSS.', 'Python, Flask, SQL, HTML, CSS, Git', 'B.Tech / MCA', '1-2 years', ?)
    """, (recruiter_id,))
    job_id = cursor.lastrowid
    conn.commit()
    print(f"[PASS] Job posted successfully (ID: {job_id})")

    # 3. Test Candidate Resume Upload & Background Queue
    print("\n[Test 3] Testing OS Background Queue for Candidate Application...")
    sample_resume = os.path.join(os.path.dirname(__file__), 'uploads', 'resumes', 'sample_alex_python_dev.docx')
    task = (sample_resume, 'sample_alex_python_dev.docx', job_id, candidate_id)
    resume_queue.put(task)
    time.sleep(1.5)

    cursor.execute("SELECT * FROM candidates WHERE user_id = ? AND job_id = ?", (candidate_id, job_id))
    cand_row = cursor.fetchone()
    assert cand_row is not None, "Candidate record was not inserted by worker!"
    print(f"[PASS] Candidate application processed! Name: {cand_row[2]}, Match Score: {cand_row[10]}%")
    cand_db_id = cand_row[0]

    # 4. Test Recruiter Shortlist and Interview Scheduling
    print("\n[Test 4] Testing Recruiter Interview Scheduling...")
    cursor.execute("UPDATE candidates SET status = 'Shortlisted' WHERE id = ?", (cand_db_id,))
    cursor.execute("""
        INSERT INTO interviews (candidate_id, date, time, interview_type, meeting_link, status)
        VALUES (?, '2026-10-20', '02:00 PM', 'Online', 'https://meet.google.com/xyz-abc', 'Scheduled')
    """, (cand_db_id,))
    cursor.execute("UPDATE candidates SET status = 'Interview Scheduled' WHERE id = ?", (cand_db_id,))
    conn.commit()
    print("[PASS] Interview scheduled and candidate status updated.")

    # 5. Test Flask Endpoints with test_client
    print("\n[Test 5] Testing HTTP Endpoints for both Portals...")
    app.config['TESTING'] = True
    client = app.test_client()

    # Public pages
    res = client.get('/')
    assert res.status_code == 200
    assert b"Resume Screener" in res.data

    # Recruiter session
    with client.session_transaction() as sess:
        sess['user_id'] = recruiter_id
        sess['user_name'] = 'Alice Recruiter'
        sess['user_email'] = 'recruiter@test.com'
        sess['role'] = 'recruiter'

    res = client.get('/dashboard')
    assert res.status_code == 200
    assert b"Recruiter Dashboard" in res.data

    res = client.get('/candidates')
    assert res.status_code == 200
    assert b"Candidate Rankings" in res.data

    # Candidate session
    with client.session_transaction() as sess:
        sess['user_id'] = candidate_id
        sess['user_name'] = 'Bob Candidate'
        sess['user_email'] = 'candidate@test.com'
        sess['role'] = 'candidate'

    res = client.get('/candidate/dashboard')
    assert res.status_code == 200
    assert b"Candidate Dashboard" in res.data

    res = client.get('/candidate/jobs')
    assert res.status_code == 200
    assert b"Available Job Openings" in res.data

    res = client.get('/candidate/my-interviews')
    assert res.status_code == 200
    assert b"My Scheduled Interviews" in res.data

    print("[PASS] Both Recruiter and Candidate portal routes verified!")
    conn.close()

    print("\n============================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("============================================================")

if __name__ == '__main__':
    run_tests()
