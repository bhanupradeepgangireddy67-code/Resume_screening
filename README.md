# Resume Screening and Candidate Ranking System

A full-stack, modular web application built for college project demonstration and evaluation in **Computer Science & Engineering (Data Science)**.

The system automates the recruitment pipeline by extracting candidate details from PDF/DOCX resumes, mathematically computing relevance scores against job descriptions using **TF-IDF & Cosine Similarity**, asynchronously managing processing using **Operating Systems Producer-Consumer multithreading**, and providing a **recruitment management & analytics dashboard**.

---

## 1. Project Objectives
- Enable recruiters to create and manage job descriptions with required skill tags.
- Support resume uploads in both **PDF** (`.pdf`) and **Word** (`.docx`) formats.
- Automatically parse candidate resumes to extract name, email, phone number, technical skills, education, and experience.
- Calculate real, mathematical match scores using NLP (TF-IDF vectorization and Cosine Similarity) without fake numbers.
- Rank candidates from highest to lowest score on a clean leaderboard.
- Allow recruiters to shortlist or reject candidates with live status updates.
- Provide interview scheduling (Online & Offline) with Google Meet/Zoom links.
- Render dynamic visual recruitment analytics using **Chart.js** directly from **SQLite**.
- Demonstrate core **Operating Systems concepts** with an asynchronous background worker queue.

---

## 2. Four Integrated Academic Domains

### A. Machine Learning / NLP
- **TF-IDF Vectorization (`scikit-learn`):** Converts job descriptions and candidate resume texts into numerical term-frequency inverse-document-frequency vectors with English stop-word filtering.
- **Cosine Similarity:** Calculates the angle between the two multidimensional document vectors:
  $$\text{Cosine Similarity}(\vec{A}, \vec{B}) = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$$
- **Score Calculation:** Converts similarity to a percentage ($0\%$ to $100\%$) and provides skill gap analysis (Matched vs. Missing Skills).

### B. Full Stack Development
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons, Chart.js.
- **Backend:** Python, Flask web framework, Jinja2 templating.
- **Database:** SQLite relational database (`database.db`).
- **RESTful Architecture:** Clean routes, form handling, session-based role authentication, and file management.

### C. Software Engineering
- **Modular Directory Structure:** Distinct separation between backend (`app.py`), ML logic (`ml/`), resume parsing utilities (`utils/`), frontend templates (`templates/`), and static assets (`static/`).
- **Security & Integrity:** Werkzeug password hashing, session tokens, secure filename sanitation, and SQL parameterized queries preventing injection.
- **Error Handling & Validation:** User-friendly flash feedback for duplicate accounts, invalid file formats, and missing parameters.

### D. Operating Systems
- **Producer-Consumer Architecture:** 
  - **Producer:** Web HTTP handler receives file uploads and immediately enqueues tasks in `queue.Queue`.
  - **Queue:** Synchronized thread-safe FIFO buffer holding processing tasks.
  - **Consumer (Worker Thread):** Background daemon thread running via `threading.Thread` dequeues items, parses files, executes ML vector math, and updates SQLite without blocking the UI.

---

## 3. Project Folder Structure

```plaintext
Resume_screening/
│
├── app.py                     # Main Flask backend & OS worker queue
├── database.db                # SQLite database (auto-created on startup)
├── requirements.txt           # Python dependencies
├── README.md                  # Complete documentation & viva guide
│
├── templates/                 # Frontend Jinja2 HTML templates
│   ├── base.html              # Base layout (Navbar, Sidebar, Flash alerts)
│   ├── index.html             # Professional landing page
│   ├── login.html             # Recruiter login page
│   ├── register.html          # Recruiter registration page
│   ├── dashboard.html         # Live recruiter dashboard
│   ├── create_job.html        # Job creation form
│   ├── edit_job.html          # Job editing form
│   ├── jobs.html              # Job openings management table
│   ├── job_details.html       # Job details & applicants list
│   ├── candidates.html        # Ranked candidate leaderboard
│   ├── candidate_details.html # Candidate profile & skill gap analysis
│   ├── schedule.html          # Interview scheduling modal/page
│   ├── interviews.html        # Interview management table
│   └── analytics.html         # Visual recruitment charts (Chart.js)
│
├── static/
│   ├── css/
│   │   └── style.css          # Modern HR theme stylesheet
│   └── js/
│       └── script.js          # Interactive UX, drag-drop, delete alerts
│
├── uploads/
│   └── resumes/               # Uploaded PDF and DOCX storage
│
├── ml/
│   ├── __init__.py
│   ├── preprocessing.py       # Text cleaning & stop-word normalization
│   └── ranking.py             # TF-IDF & Cosine Similarity calculator
│
└── utils/
    ├── __init__.py
    └── resume_parser.py       # pypdf, python-docx, and regex extractors
```

---

## 4. Database Schema (SQLite)

Tables are automatically generated on first run:

1. **`users`**:
   - `id` (INTEGER PRIMARY KEY)
   - `name`, `email` (UNIQUE), `password` (hashed), `role`, `created_at`

2. **`jobs`**:
   - `id` (INTEGER PRIMARY KEY)
   - `title`, `description`, `skills`, `education`, `experience`, `created_by`, `created_at`

3. **`candidates`**:
   - `id` (INTEGER PRIMARY KEY)
   - `name`, `email`, `phone`, `resume_filename`, `resume_text`
   - `skills`, `education`, `experience`, `match_score`, `status`, `job_id`, `created_at`
   - Statuses: `Pending`, `Shortlisted`, `Rejected`, `Interview Scheduled`

4. **`interviews`**:
   - `id` (INTEGER PRIMARY KEY)
   - `candidate_id`, `date`, `time`, `interview_type` (`Online`/`Offline`), `meeting_link`, `status` (`Scheduled`/`Completed`/`Cancelled`), `created_at`

---

## 5. Installation & Setup Instructions

### Step 1: Open Terminal in Project Folder
```powershell
cd c:\Users\lenovo\Desktop\Resume_screening
```

### Step 2: (Optional) Create and Activate Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Application
```powershell
python app.py
```

### Step 5: Open in Web Browser
Visit:
```
http://127.0.0.1:5000
```

---

## 6. End-to-End Walkthrough & Demonstration Steps

1. **Registration:**
   - Open `http://127.0.0.1:5000` and click **"Get Started"** or **"Register"**.
   - Create a recruiter account (e.g., Name: `Suresh Sharma`, Email: `recruiter@techcorp.com`, Password: `password123`).
2. **Login:**
   - Sign in with your registered credentials.
3. **Post a Job:**
   - Navigate to **Jobs** $\rightarrow$ **"Post New Job"**.
   - Example Title: `Python Backend Developer`
   - Required Skills: `Python, Flask, SQL, Git, REST API`
   - Experience: `1-3 years`
   - Enter job description and click **"Create Job"**.
4. **Apply for a Job:**
   - Register or sign in as a candidate.
   - Open **"View Jobs"**, choose an opening, and upload a `.pdf` or `.docx` resume.
   - The OS producer-consumer background worker asynchronously extracts text, parses skills, and calculates the TF-IDF match score.
5. **Leaderboard & Candidate Ranking:**
   - Visit **Candidates** to view ranked candidates sorted by match score.
   - Click **"View"** to inspect extracted skills, contact information, matched skills vs. missing skills.
6. **Shortlist / Reject:**
   - Click **"Shortlist Candidate"** or **"Reject Candidate"**. Notice the dashboard counters update dynamically.
7. **Schedule Interview:**
   - Click **"Schedule Interview"** on a shortlisted candidate.
   - Pick Date, Time, Format (`Online`), and Google Meet link.
   - View scheduled interviews under the **Interviews** page.
8. **View Analytics:**
   - Open the **Analytics** page to observe live Chart.js distributions (Candidate Status, Score Ranges, Applicants per Job).

---

## 7. College Viva Guide & Quick Answers

- **Machine Learning Viva Question:** *"How does the system rank resumes?"*
  - **Answer:** *"The system takes the combined job description text and the candidate's parsed resume text, cleans them using regular expressions and stop-word removal, and transforms them into TF-IDF vectors using scikit-learn. We then compute the Cosine Similarity between the two vectors, which yields a mathematical value between 0.0 and 1.0, representing the semantic and keyword alignment, and convert it into a match percentage."*

- **Operating Systems Viva Question:** *"Where is the OS concept used in this project?"*
  - **Answer:** *"We implemented the Producer-Consumer problem using Python's `queue.Queue` and `threading.Thread`. When a recruiter uploads a resume, the web request thread acts as a producer and enqueues a job without blocking. A background daemon worker thread acts as the consumer, continuously pulling tasks from the queue and performing CPU-intensive resume parsing and NLP matching in the background."*

- **Software Engineering Viva Question:** *"What software engineering principles were followed?"*
  - **Answer:** *"The project follows modular design and separation of concerns. ML ranking algorithms are isolated in the `ml/` package, parsing utilities in `utils/`, presentation templates in `templates/`, and routes in `app.py`. We used Werkzeug password hashing for security, SQL parameterized queries to prevent SQL injection, and centralized error handling with user-friendly alerts."*
