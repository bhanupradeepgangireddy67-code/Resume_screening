"""
Candidate Ranking & ML Module
Domain: Machine Learning / NLP

Implements TF-IDF vectorization and Cosine Similarity to calculate
real, mathematical relevance scores between resumes and job postings.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ml.preprocessing import clean_text

def calculate_match_score(job_text_combined, resume_text_combined):
    """
    Calculates TF-IDF and Cosine Similarity between Job text and Resume text.

    Steps:
    1. Preprocess and clean both texts.
    2. Convert texts into TF-IDF numerical vectors.
    3. Compute cosine similarity between the two vectors.
    4. Convert similarity (range 0.0 to 1.0) into percentage (0.0% to 100.0%).
    """
    clean_job = clean_text(job_text_combined)
    clean_resume = clean_text(resume_text_combined)

    # Edge cases: if either text is empty
    if not clean_job or not clean_resume:
        return 0.0

    try:
        # Initialize TfidfVectorizer with English stop-word filtering
        vectorizer = TfidfVectorizer(stop_words='english')
        
        # Fit and transform the two documents into TF-IDF space
        tfidf_matrix = vectorizer.fit_transform([clean_job, clean_resume])
        
        # Calculate Cosine Similarity: dot product divided by magnitudes
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # Convert to percentage and round to 2 decimal places
        match_score = round(float(similarity) * 100, 2)
        
        # Bound score between 0 and 100
        return max(0.0, min(100.0, match_score))
    except Exception as e:
        print(f"[ML Error] Failed to calculate TF-IDF similarity: {e}")
        return 0.0

def evaluate_candidate_for_job(job, candidate_data):
    """
    Evaluates a candidate against a specific job record.
    
    Job text = Description + Required Skills + Education + Experience
    Resume text = Extracted Resume Text + Extracted Skills + Candidate Education + Experience
    """
    job_text = (
        f"{job.get('title', '')} "
        f"{job.get('description', '')} "
        f"{job.get('skills', '')} "
        f"{job.get('education', '')} "
        f"{job.get('experience', '')}"
    )

    resume_text = (
        f"{candidate_data.get('raw_text', '')} "
        f"{candidate_data.get('skills', '')} "
        f"{candidate_data.get('education', '')} "
        f"{candidate_data.get('experience', '')}"
    )

    score = calculate_match_score(job_text, resume_text)
    return score

def extract_skill_comparison(required_skills_str, candidate_skills_str):
    """
    Compares required skills with candidate skills.
    Returns matched skills and missing skills.
    """
    if not required_skills_str:
        return [], []

    # Split comma-separated skills and normalize
    required = [s.strip() for s in required_skills_str.split(",") if s.strip()]
    candidate = [s.strip().lower() for s in candidate_skills_str.split(",") if s.strip()]

    matched = []
    missing = []

    for req in required:
        if req.lower() in candidate:
            matched.append(req)
        else:
            missing.append(req)

    return matched, missing
