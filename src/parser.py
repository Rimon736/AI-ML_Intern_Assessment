import fitz  # PyMuPDF
import re
from typing import Dict
from src.config import PDF_PATH
from src.config import OUTPUT_DIR, logger

def extract_sections_from_pdf() -> Dict[int, str]:
    """
    Extracts text from the PDF and splits it into sections.
    Returns a dictionary mapping section_id (int) to section_text (str).
    """
    try:
        doc = fitz.open(PDF_PATH)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
            
        doc.close()
        
        # Clean up PDF artifacts (page headers, footers, and metadata)
        full_text = re.sub(r'--- PAGE \d+ ---', '', full_text)
        full_text = re.sub(r'SLATEFALL_DOSSIER\.md', '', full_text)
        full_text = re.sub(r'2026-05-18', '', full_text)
        full_text = re.sub(r'\n\d{1,2}/50\n', '\n', full_text)

    except Exception as e:
        raise FileNotFoundError(f"Failed to read PDF at {PDF_PATH}. Ensure the file exists. Error: {e}")

    # Regex to find "Section 1. ...", "Section 2. ...", up to the next section or end of file
    # We use a lookahead (?=...) to stop capturing when the next section begins
    pattern = re.compile(r"Section (\d+)\.\s(.*?)(?=Section \d+\.\s|$)", re.DOTALL)
    matches = pattern.findall(full_text)
    
    sections = {}
    for match in matches:
        section_id = int(match[0])
        section_text = match[1].strip()
        sections[section_id] = section_text
        
    if not sections:
        logger.info("Warning: Could not parse sections using regex. Check PDF text format.")
        
    return sections