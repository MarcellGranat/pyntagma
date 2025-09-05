from pathlib import Path

from src.pyntagma import Crop

# Create crops with the actual 2-part PDF files
test_crop = Crop(
    path=Path("tests/test_pdfs/test-1.pdf"),
    page_number=0,
    x0=10.0,
    x1=90.0,
    top=20.0,
    bottom=80.0,
    padding=5,
    resolution=300
)

test_crop_part2 = Crop(
    path=Path("tests/test_pdfs/test-2.pdf"),
    page_number=0,
    x0=10.0,
    x1=90.0,
    top=20.0,
    bottom=80.0
)


def test_crop_creation():
    """Test Crop creation and basic properties."""
    assert test_crop.path == Path("tests/test_pdfs/test-1.pdf")
    assert test_crop.page_number == 0
    assert test_crop.x0 == 10.0
    assert test_crop.x1 == 90.0
    assert test_crop.top == 20.0
    assert test_crop.bottom == 80.0
    assert test_crop.padding == 5
    assert test_crop.resolution == 300


def test_crop_string_representation():
    """Test Crop string representations."""
    str_repr = str(test_crop)
    assert "Crop" in str_repr
    assert "x0=10.0" in str_repr
    assert "x1=90.0" in str_repr
    
    repr_str = repr(test_crop)
    assert "Crop" in repr_str


def test_crop_hash():
    """Test Crop hash functionality."""
    crop1 = Crop(
        path=Path("tests/test_pdfs/test-1.pdf"),
        page_number=0,
        x0=10.0,
        x1=90.0,
        top=20.0,
        bottom=80.0
    )
    
    crop2 = Crop(
        path=Path("tests/test_pdfs/test-1.pdf"),
        page_number=0,
        x0=10.0,
        x1=90.0,
        top=20.0,
        bottom=80.0
    )
    
    # Same crops should have same hash
    assert hash(crop1) == hash(crop2)


def test_crop_defaults():
    """Test Crop default values."""
    assert test_crop_part2.padding == 0
    assert test_crop_part2.resolution == 600


def test_crop_two_part_pdf():
    """Test Crop with both parts of the 2-part PDF."""
    # Both should be valid Crop objects
    assert isinstance(test_crop, Crop)
    assert isinstance(test_crop_part2, Crop)
    
    # They should have different paths
    assert test_crop.path != test_crop_part2.path
    assert "test-1.pdf" in str(test_crop.path)
    assert "test-2.pdf" in str(test_crop_part2.path)
