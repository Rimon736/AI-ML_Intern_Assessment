import pytest
import os
from src.db import init_db
from src.parser import extract_sections_from_pdf

def test_database_initialization():
    """Test that the DB initializes without crashing."""
    try:
        init_db()
        assert os.path.exists("knowledge_base.sqlite")
    except Exception as e:
        pytest.fail(f"DB init failed: {e}")

def test_pdf_parser_handles_missing_file():
    """Test graceful error handling for missing PDF."""
    # Temporarily rename file if it exists to force an error
    original = "SLATEFALL_DOSSIER.pdf"
    temp = "TEMP_DOSSIER.pdf"
    if os.path.exists(original):
        os.rename(original, temp)
        
    with pytest.raises(FileNotFoundError):
        extract_sections_from_pdf()
        
    # Restore
    if os.path.exists(temp):
        os.rename(temp, original)