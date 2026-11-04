"""
ML Preprocessing Module
Domain: Machine Learning / Natural Language Processing (NLP)

This module handles text cleaning and preprocessing tasks:
- Lowercasing text
- Removing punctuation and special symbols
- Normalizing whitespace
"""

import re

# Common English stop words for quick filtering if needed
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any',
    'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between',
    'both', 'but', 'by', 'can', 'did', 'do', 'does', 'doing', 'down', 'during', 'each',
    'few', 'for', 'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here',
    'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is',
    'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor',
    'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours',
    'ourselves', 'out', 'over', 'own', 's', 'same', 'she', 'should', 'so', 'some', 'such',
    't', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
    'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up',
    'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom',
    'why', 'will', 'with', 'you', 'your', 'yours', 'yourself', 'yourselves'
}

def clean_text(text):
    """
    Cleans raw text for NLP processing.
    1. Converts text to lowercase.
    2. Removes URLs, non-alphanumeric noise while preserving tech symbols like c++, c#, .net.
    3. Collapses multiple whitespace characters into a single space.
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)

    # Remove email addresses from matching text (emails are captured separately)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' ', text)

    # Replace special punctuation (except + and # often found in C++, C#)
    text = re.sub(r'[^a-zA-Z0-9+#\s.]', ' ', text)

    # Remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def remove_stopwords(text):
    """
    Removes common stop words from a string of text.
    Useful for keyword density analysis.
    """
    words = text.split()
    filtered = [w for w in words if w.lower() not in STOP_WORDS]
    return ' '.join(filtered)
