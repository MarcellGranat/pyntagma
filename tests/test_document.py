import io
from pathlib import Path

from src.pyntagma import Document

# Create a document with the actual 2-part PDF files
test_files = [Path("tests/test_pdfs/test-1.pdf"), Path("tests/test_pdfs/test-2.pdf")]

doc = Document(files=test_files)


def test_document_creation():
    """Test creating a document with the 2-part PDF files."""
    assert isinstance(doc, Document)
    assert len(doc.files) == 2


def test_document_two_part_creation():
    """test creating a document with both parts of the 2-part pdf."""
    assert isinstance(doc, Document)
    assert len(doc.files) == 2

    # check that both parts are included
    file_names = [f.name for f in doc.files]
    assert "test-1.pdf" in file_names
    assert "test-2.pdf" in file_names


def test_show_same():
    """Test that the same show is the same."""
    # Plot the first word
    plot1 = doc.pages[0].plot_on([doc.pages[0].words[0]], colors=["red"])
    buffer1 = io.BytesIO()
    plot1.save(buffer1, format="PNG")
    buffer1.seek(0)

    # Plot the first word again
    plot1b = doc.pages[0].plot_on([doc.pages[0].words[0]], colors=["red"])
    buffer1b = io.BytesIO()
    plot1b.save(buffer1b, format="PNG")
    buffer1b.seek(0)

    plot2 = doc.pages[0].words[0].plot_on_page(color="red")
    buffer2 = io.BytesIO()
    plot2.save(buffer2, format="PNG")
    buffer2.seek(0)

    # Plot the second word
    plot3 = doc.pages[0].plot_on([doc.pages[0].words[1]], colors=["red"])
    buffer3 = io.BytesIO()
    plot3.save(buffer3, format="PNG")
    buffer3.seek(0)

    # The first two identical plots should be the same
    assert buffer1.read() == buffer1b.read()

    # same plot from different method should be the same
    buffer1.seek(0)
    assert buffer1.read() == buffer2.read()

    # different plots should not be the same
    buffer1.seek(0)
    assert buffer1.read() != buffer3.read()
