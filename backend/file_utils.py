import PyPDF2
import io
from docx import Document

def read_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return ""
    file_extension = uploaded_file.name.lower().split('.')[-1]
    try:
        if file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif file_extension == 'docx':
            doc = Document(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        elif file_extension == 'txt':
            return uploaded_file.getvalue().decode("utf-8")
        else:
            return None
    except Exception as e:
        return None 