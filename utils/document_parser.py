import os
import tempfile
from typing import Optional
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

def parse_document(file_path: str, content_type: str) -> Optional[str]:
    """Parse document and extract text content"""
    try:
        if content_type == 'application/pdf':
            return parse_pdf(file_path)
        elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return parse_docx(file_path)
        elif content_type == 'application/msword':
            return parse_doc(file_path)
        elif content_type == 'text/plain':
            return parse_txt(file_path)
        elif content_type == 'text/csv':
            return parse_csv(file_path)
        elif content_type == 'application/rtf':
            return parse_rtf(file_path)
        elif content_type in ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff']:
            return parse_image_with_ocr(file_path)
        else:
            # Try to detect file type by extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                return parse_image_with_ocr(file_path)
            elif file_ext == '.pdf':
                return parse_pdf(file_path)
            return None
    except Exception as e:
        print(f"Error parsing document {file_path}: {e}")
        return None

def parse_pdf(file_path: str) -> Optional[str]:
    """Parse PDF file with OCR fallback"""
    try:
        import PyPDF2
        
        # First try to extract text directly
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n"
            
            # If we got meaningful text, return it
            if text.strip() and len(text.strip()) > 50:
                return text.strip()
            
            # If text extraction failed or returned little text, try OCR
            print("PDF text extraction returned little text, trying OCR...")
            return parse_pdf_with_ocr(file_path)
            
    except ImportError:
        print("PyPDF2 not installed. Install with: pip install PyPDF2")
        return parse_pdf_with_ocr(file_path)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return parse_pdf_with_ocr(file_path)

def parse_pdf_with_ocr(file_path: str) -> Optional[str]:
    """Parse PDF using OCR"""
    try:
        print("Converting PDF to images for OCR...")
        
        # Convert PDF to images
        images = convert_from_path(file_path, dpi=300)
        
        if not images:
            print("No images extracted from PDF")
            return None
        
        text = ""
        print(f"Processing {len(images)} pages with OCR...")
        
        for i, image in enumerate(images):
            print(f"Processing page {i + 1}/{len(images)}...")
            
            # Convert PIL image to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Use OCR to extract text
            page_text = pytesseract.image_to_string(image, lang='rus+eng')
            text += page_text + "\n"
        
        return text.strip()
        
    except Exception as e:
        print(f"Error in PDF OCR: {e}")
        return None

def parse_image_with_ocr(file_path: str) -> Optional[str]:
    """Parse image file using OCR"""
    try:
        print(f"Processing image with OCR: {file_path}")
        
        # Open image
        image = Image.open(file_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Use OCR to extract text
        text = pytesseract.image_to_string(image, lang='rus+eng')
        
        return text.strip()
        
    except Exception as e:
        print(f"Error in image OCR: {e}")
        return None

def parse_docx(file_path: str) -> Optional[str]:
    """Parse DOCX file"""
    try:
        from docx import Document
        
        doc = Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except ImportError:
        print("python-docx not installed. Install with: pip install python-docx")
        return None
    except Exception as e:
        print(f"Error parsing DOCX: {e}")
        return None

def parse_doc(file_path: str) -> Optional[str]:
    """Parse DOC file (legacy Word format)"""
    try:
        import subprocess
        import tempfile
        
        # Convert DOC to DOCX using LibreOffice
        temp_dir = tempfile.mkdtemp()
        temp_docx = os.path.join(temp_dir, "temp.docx")
        
        # Try to convert using LibreOffice
        result = subprocess.run([
            'libreoffice', '--headless', '--convert-to', 'docx', 
            '--outdir', temp_dir, file_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(temp_docx):
            text = parse_docx(temp_docx)
            os.remove(temp_docx)
            os.rmdir(temp_dir)
            return text
        else:
            # Fallback: try to read as plain text
            return parse_txt(file_path)
            
    except Exception as e:
        print(f"Error parsing DOC: {e}")
        return None

def parse_txt(file_path: str) -> Optional[str]:
    """Parse plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except UnicodeDecodeError:
        # Try with different encodings
        encodings = ['latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read().strip()
            except UnicodeDecodeError:
                continue
        return None
    except Exception as e:
        print(f"Error parsing TXT: {e}")
        return None

def parse_csv(file_path: str) -> Optional[str]:
    """Parse CSV file"""
    try:
        import csv
        
        text = ""
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                text += " ".join(row) + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return None

def parse_rtf(file_path: str) -> Optional[str]:
    """Parse RTF file"""
    try:
        import subprocess
        import tempfile
        
        # Try to convert RTF to plain text using LibreOffice
        temp_dir = tempfile.mkdtemp()
        temp_txt = os.path.join(temp_dir, "temp.txt")
        
        result = subprocess.run([
            'libreoffice', '--headless', '--convert-to', 'txt', 
            '--outdir', temp_dir, file_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(temp_txt):
            text = parse_txt(temp_txt)
            os.remove(temp_txt)
            os.rmdir(temp_dir)
            return text
        else:
            # Fallback: try to read as plain text
            return parse_txt(file_path)
            
    except Exception as e:
        print(f"Error parsing RTF: {e}")
        return None

def get_file_info(file_path: str) -> dict:
    """Get basic file information"""
    try:
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'extension': os.path.splitext(file_path)[1].lower()
        }
    except Exception as e:
        print(f"Error getting file info: {e}")
        return {}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"
