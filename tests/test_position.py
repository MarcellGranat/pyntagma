from unittest.mock import Mock

import pytest

from src.pyntagma import (
    HorizontalCoordinate,
    HorizontalPosition,
    Position,
    VerticalCoordinate,
    VerticalPosition,
    get_position,
    left_position_join,
)


def create_mock_page(height=100, width=100, page_number=0):
    """Create a mock page for testing."""
    mock_page = Mock()
    mock_page.height = height
    mock_page.width = width
    mock_page.page_number = page_number
    return mock_page


def test_vertical_coordinate():
    """Test VerticalCoordinate functionality."""
    page = create_mock_page()
    coord = VerticalCoordinate(page=page, value=50.0)
    
    assert coord.value == 50.0
    assert coord.relative == 0.5
    assert coord.page_number == 0


def test_horizontal_coordinate():
    """Test HorizontalCoordinate functionality."""
    page = create_mock_page()
    coord = HorizontalCoordinate(page=page, value=25.0)
    
    assert coord.value == 25.0
    assert coord.relative == 0.25
    assert coord.page_number == 0


def test_position_creation():
    """Test Position creation and properties."""
    page = create_mock_page()
    
    x0 = HorizontalCoordinate(page=page, value=10.0)
    x1 = HorizontalCoordinate(page=page, value=90.0)
    top = VerticalCoordinate(page=page, value=20.0)
    bottom = VerticalCoordinate(page=page, value=80.0)
    
    position = Position(x0=x0, x1=x1, top=top, bottom=bottom)
    
    assert isinstance(position.vertical, VerticalPosition)
    assert isinstance(position.horizontal, HorizontalPosition)


def test_position_contains():
    """Test Position.contains method."""
    page = create_mock_page()
    
    # Create outer position
    outer_pos = Position(
        x0=HorizontalCoordinate(page=page, value=0.0),
        x1=HorizontalCoordinate(page=page, value=100.0),
        top=VerticalCoordinate(page=page, value=0.0),
        bottom=VerticalCoordinate(page=page, value=100.0)
    )
    
    # Create inner position
    inner_pos = Position(
        x0=HorizontalCoordinate(page=page, value=10.0),
        x1=HorizontalCoordinate(page=page, value=90.0),
        top=VerticalCoordinate(page=page, value=10.0),
        bottom=VerticalCoordinate(page=page, value=90.0)
    )
    
    assert outer_pos.contains(inner_pos)
    assert not inner_pos.contains(outer_pos)


def test_get_position():
    """Test get_position utility function."""
    page = create_mock_page()
    
    position = Position(
        x0=HorizontalCoordinate(page=page, value=0.0),
        x1=HorizontalCoordinate(page=page, value=100.0),
        top=VerticalCoordinate(page=page, value=0.0),
        bottom=VerticalCoordinate(page=page, value=100.0)
    )
    
    # Test with Position object
    assert get_position(position) == position
    
    # Test with object that has position property
    mock_obj = Mock()
    mock_obj.position = position
    assert get_position(mock_obj) == position
    
    # Test with invalid object
    with pytest.raises(ValueError):
        get_position("invalid")


def test_left_position_join():
    """Test left_position_join function."""
    page = create_mock_page()
    
    # Create mock objects with positions
    item1 = Mock()
    item1.position = Mock()
    item1.position.vertical = VerticalPosition(
        top=VerticalCoordinate(page=page, value=10.0),
        bottom=VerticalCoordinate(page=page, value=20.0)
    )
    
    item2 = Mock()
    item2.position = Mock()
    item2.position.vertical = VerticalPosition(
        top=VerticalCoordinate(page=page, value=30.0),
        bottom=VerticalCoordinate(page=page, value=40.0)
    )
    
    x_items = [item1]
    y_items = [item2]
    
    # Test joining
    results = list(left_position_join(x_items, y_items, after=True))
    assert len(results) == 1
    assert results[0] == (item1, item2)
