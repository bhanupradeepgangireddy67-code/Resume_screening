"""
Resume Parser Module
Domain: Software Engineering & Data Processing

Extracts structured information from candidate resumes:
- Supports PDF (.pdf) via pypdf
- Supports Word Document (.docx) via python-docx
- Extracts candidate Contact Info (Email, Phone, Name)
- Identifies Skills, Education, and Experience via rule-based heuristics
"""

import os
import re
from pypdf import PdfReader
from docx import Document

# Predefined list of technical and data science skills for screening
PREDEFINED_SKILLS = [
    "Python", "Java", "C", "C++", "C#", "SQL", "MySQL", "PostgreSQL", "SQLite",
    "HTML", "CSS", "JavaScript", "TypeScript", "React", "Node.js", "Angular", "Vue",
    "Flask", "Django", "Spring Boot", "FastAPI",
    "Machine Learning", "Deep Learning", "Data Science", "Data Analysis",
    "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "Keras", "PyTorch", "NLP",
    "Power BI", "Tableau", "Excel", "Data Visualization",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Linux",
    "Git", "GitHub", "REST API", "MongoDB", "R"
]

# Educational degree keywords to look for
DEGREE_KEYWORDS = [
    "Ph.D", "PhD", "Doctorate",
    "M.Tech", "M.E.", "MCA", "M.Sc", "MS", "Master of Technology", "Master of Science",
    "Master of Computer Applications", "MBA", "Masters",
    "B.Tech", "B.E.", "BCA", "B.Sc", "BS", "Bachelor of Technology", "Bachelor of Engineering",
    "Bachelor of Computer Applications", "Bachelor of Science", "Bachelors", "Diploma"
]

def extract_text_from_pdf(filepath):
    """
    Extracts text from a PDF file using pypdf.
    """
    text = ""
    try:
        reader = PdfReader(filepath)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"[Error] Failed to read PDF {filepath}: {e}")
    return text.strip()

def extract_text_from_docx(filepath):
    """
    Extracts text from a DOCX file using python-docx.
    """
    text = ""
    try:
        doc = Document(filepath)
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text += paragraph.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text:
                        text += cell.text + " "
                text += "\n"
    except Exception as e:
        print(f"[Error] Failed to read DOCX {filepath}: {e}")
    return text.strip()

def extract_resume_text(filepath):
    """
    Detects file extension and routes to appropriate extraction function.
    Supports .pdf and .docx files.
    """
    if not os.path.exists(filepath):
        return ""
    
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext == ".docx":
        return extract_text_from_docx(filepath)
    else:
        # Fallback for plain text files
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

def extract_email(text):
    """
    Extracts email address using regular expression.
    """
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(pattern, text)
    return matches[0] if matches else ""

def extract_phone(text):
    """
    Extracts telephone or mobile numbers using regular expression.
    Matches standard 10-digit Indian/international mobile numbers.
    """
    # Matches formats like: +91 9876543210, 9876543210, +1-555-555-5555, (555) 555-5555
    pattern = r'(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b[6-9]\d{9}\b)'
    matches = re.findall(pattern, text)
    if matches:
        cleaned_phone = re.sub(r'[^\d+]', '', matches[0])
        return cleaned_phone if len(cleaned_phone) >= 10 else matches[0]
    return ""

def extract_skills(text):
    """
    Identifies skills by searching for predefined skill keywords in the resume text.
    Uses case-insensitive word matching.
    """
    found_skills = []
    text_lower = f" {text.lower()} "

    for skill in PREDEFINED_SKILLS:
        skill_clean = skill.lower()
        # Escape special characters like ++ or # in regex
        escaped_skill = re.escape(skill_clean)
        # Match whole word boundaries
        pattern = r'(?:^|[\s,;()\.\-\/])' + escaped_skill + r'(?:$|[\s,;()\.\-\/])'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
            
    return list(dict.fromkeys(found_skills))  # Preserve order, remove duplicates

def extract_education(text):
    """
    Identifies educational qualifications using simple keyword matching.
    """
    found_degrees = []
    text_lower = text.lower()

    for degree in DEGREE_KEYWORDS:
        pattern = r'\b' + re.escape(degree.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_degrees.append(degree)

    if found_degrees:
        return ", ".join(list(dict.fromkeys(found_degrees)))
    
    # Check for general education keywords
    if "computer science" in text_lower or "information technology" in text_lower:
        return "B.Tech in Computer Science / IT"
    
    return "Not specified"

def extract_experience(text):
    """
    Extracts years of experience mentioned in resume text.
    Looks for patterns like '3 years', '2+ yrs', 'Fresher', etc.
    """
    text_lower = text.lower()

    # Look for fresher indicators
    if "fresher" in text_lower or "entry level" in text_lower or "recent graduate" in text_lower:
        return "Fresher (0 years)"

    # Look for numeric patterns like '3+ years of experience' or '2 yrs'
    pattern = r'(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?)(?:\s*(?:of\s*)?experience)?'
    matches = re.findall(pattern, text_lower)
    if matches:
        # Take the maximum reasonable number found (typically <= 30)
        valid_nums = [float(m) for m in matches if float(m) <= 30]
        if valid_nums:
            max_years = max(valid_nums)
            return f"{int(max_years) if max_years.is_integer() else max_years} years"
    
    return "Not specified"

def extract_name(text, email=""):
    """
    Extracts candidate name using simple heuristics:
    1. Looks at the first few non-empty lines of the resume.
    2. Filters out headers or common words like 'resume', 'curriculum vitae'.
    3. Falls back to formatting email username if name line isn't obvious.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    ignore_words = ["resume", "curriculum vitae", "cv", "profile", "contact", "email", "phone", "education", "experience"]
    
    for line in lines[:5]:
        cleaned = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        words = cleaned.split()
        if 1 <= len(words) <= 4:
            if not any(ign in cleaned.lower() for ign in ignore_words):
                # Looks like a valid name
                return cleaned.title()

    # Fallback to email name
    if email and "@" in email:
        email_name = email.split("@")[0]
        # remove numbers and underscores
        cleaned_name = re.sub(r'[^a-zA-Z]', ' ', email_name).strip()
        if cleaned_name:
            return cleaned_name.title()

    return "Candidate"

def parse_resume(filepath):
    """
    Master function: Parses a resume file and extracts all candidate attributes.
    Returns a dictionary of extracted candidate details.
    """
    text = extract_resume_text(filepath)
    email = extract_email(text)
    phone = extract_phone(text)
    name = extract_name(text, email)
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)

    return {
        "name": name,
        "email": email or "Not provided",
        "phone": phone or "Not provided",
        "raw_text": text,
        "skills": ", ".join(skills) if skills else "None detected",
        "skills_list": skills,
        "education": education,
        "experience": experience
    }
