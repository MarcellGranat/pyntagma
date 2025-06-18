from pathlib import Path

from pyntagma import Document

# Create a document with the actual 2-part PDF files
test_files = [
        Path("tests/test_pdfs/test-1.pdf"),
        Path("tests/test_pdfs/test-2.pdf")
    ]
    
doc = Document(files=test_files)

def test_document_creation():
    """Test creating a document with the 2-part PDF files.""" 
    assert isinstance(doc, Document)
    assert len(doc.files) == 2


def test_document_two_part_creation():
    """Test creating a document with both parts of the 2-part PDF."""
    assert isinstance(doc, Document)
    assert len(doc.files) == 2
    
    # Check that both parts are included
    file_names = [f.name for f in doc.files]
    assert "test-1.pdf" in file_names
    assert "test-2.pdf" in file_names