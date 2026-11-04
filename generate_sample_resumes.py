"""
Utility Script: Generate Sample Resumes (PDF & DOCX)
Provides realistic sample resumes for project demonstration and college evaluation.
"""

import os
from docx import Document

def make_simple_pdf(filename, text_lines):
    stream = "BT /F1 12 Tf 50 750 Td 15 TL\n"
    for line in text_lines:
        safe_line = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        stream += f"({safe_line}) Tj T*\n"
    stream += "ET"
    stream_bytes = stream.encode('latin1')
    
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
        f'<< /Length {len(stream_bytes)} >>\nstream\n'.encode('latin1') + stream_bytes + b'\nendstream',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'
    ]
    
    out = b'%PDF-1.4\n'
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += f'{i} 0 obj\n'.encode('latin1') + obj + b'\nendobj\n'
    
    xref_offset = len(out)
    out += f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode('latin1')
    for off in offsets:
        out += f'{off:010d} 00000 n \n'.encode('latin1')
    out += f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF'.encode('latin1')
    
    with open(filename, 'wb') as f:
        f.write(out)

def create_all_samples():
    target_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'resumes')
    os.makedirs(target_dir, exist_ok=True)

    # 1. Sarah Miller (Data Science - PDF)
    pdf_sarah = os.path.join(target_dir, 'sample_sarah_datascience.pdf')
    make_simple_pdf(pdf_sarah, [
        'Sarah Miller',
        'Email: sarah.miller@datascience.org',
        'Phone: +91 9123456789',
        'Education: M.Tech in Data Science, 2022',
        'Skills: Python, Machine Learning, Deep Learning, Pandas, NumPy, Scikit-learn, TensorFlow, SQL, NLP',
        'Experience: 3 years of experience developing predictive analytics and ML pipelines.'
    ])

    # 2. Alex Johnson (Python Web Developer - DOCX)
    docx_alex = os.path.join(target_dir, 'sample_alex_python_dev.docx')
    doc1 = Document()
    doc1.add_heading('Alex Johnson', 0)
    doc1.add_paragraph('Email: alex.johnson@example.com | Phone: 9876543210')
    doc1.add_heading('Education', level=1)
    doc1.add_paragraph('B.Tech in Computer Science and Engineering, 2023')
    doc1.add_heading('Technical Skills', level=1)
    doc1.add_paragraph('Python, Flask, SQL, MySQL, Git, GitHub, REST API, HTML, CSS, JavaScript, Pandas')
    doc1.add_heading('Professional Experience', level=1)
    doc1.add_paragraph('Software Engineer with 2 years of experience building web backends and REST APIs in Python.')
    doc1.save(docx_alex)

    # 3. Emily Watson (Frontend Developer - PDF)
    pdf_emily = os.path.join(target_dir, 'sample_emily_frontend.pdf')
    make_simple_pdf(pdf_emily, [
        'Emily Watson',
        'Email: emily.watson@webdev.com',
        'Phone: +91 9888877777',
        'Education: B.Tech in Information Technology, 2023',
        'Skills: HTML, CSS, JavaScript, React, TypeScript, Vue, Git, GitHub',
        'Experience: 1 year of frontend development designing responsive UI components in React.'
    ])

    # 4. David Kumar (DevOps / Cloud Engineer - DOCX)
    docx_david = os.path.join(target_dir, 'sample_david_cloud.docx')
    doc2 = Document()
    doc2.add_heading('David Kumar', 0)
    doc2.add_paragraph('Email: david.kumar@cloudops.net | Phone: 9777766666')
    doc2.add_heading('Education', level=1)
    doc2.add_paragraph('B.E. in Computer Science, 2021')
    doc2.add_heading('Technical Skills', level=1)
    doc2.add_paragraph('AWS, Azure, Docker, Kubernetes, Linux, Git, GitHub, Python, SQL')
    doc2.add_heading('Professional Experience', level=1)
    doc2.add_paragraph('DevOps Engineer with 4 years of experience managing CI/CD and AWS cloud deployments.')
    doc2.save(docx_david)

    print("Sample resumes generated successfully in:", target_dir)
    print("Files created:")
    print("  1. sample_sarah_datascience.pdf (PDF format)")
    print("  2. sample_alex_python_dev.docx  (DOCX format)")
    print("  3. sample_emily_frontend.pdf    (PDF format)")
    print("  4. sample_david_cloud.docx      (DOCX format)")

if __name__ == '__main__':
    create_all_samples()
