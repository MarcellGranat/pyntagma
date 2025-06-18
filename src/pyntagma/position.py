from pydantic import BaseModel
from typing import Any, Iterable
from .pdf_reader import Crop


class VerticalCoordinate(BaseModel):
    page: Any
    value: float

    @property
    def relative(self) -> float:
        return self.value / self.page.height

    def __hash__(self):
        return hash((self.page_number, self.value))
    
    @property
    def page_number(self) -> int:
        return self.page.page_number
    
    def shift(self, delta: float) -> 'VerticalCoordinate':
        """
        Shift the vertical coordinate by a given delta.
        """
        value = self.value
        page = self.page
        while True:
            if delta > 0:
                if value + delta <= self.page.height:
                    value = value + delta 
                    return VerticalCoordinate(page=page, value=value)
                else:
                    delta -= (self.page.height - self.value)

                    if page.page_number + 1 ==  len(page.document): # reached the last page
                        value = page.height
                        return VerticalCoordinate(page=page, value=value)
                    else:
                        page = page.document.pages[page.page_number + 1]
                        value = 0
            elif delta < 0:
                if value + delta >= 0:
                    value += delta
                    return VerticalCoordinate(page=page, value=value)
                else:
                    delta += value
                    if page.page_number == 0: # already on the first page
                        return VerticalCoordinate(page=page, value=0)
                    else:
                        page = page.document.pages[page.page_number - 1]
                        value = page.height
            else:
                return VerticalCoordinate(page=page, value=value)

    
    def __lt__(self, other):
        return (
            self.page_number < other.page_number or
            (self.page_number == other.page_number and self.value < other.value)
        )
    
    def __le__(self, other):
        return (
            self.page_number < other.page_number or
            (self.page_number == other.page_number and self.value <= other.value)
        )
    
    def __gt__(self, other):
        return (
            self.page_number > other.page_number or
            (self.page_number == other.page_number and self.value > other.value)
        )
    
    def __ge__(self, other):
        return (
            self.page_number > other.page_number or
            (self.page_number == other.page_number and self.value >= other.value)
        )
    
    def __sub__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            shifted = self.shift(-other)
            return shifted

        self_before: bool = (
            self.page_number < other.page_number or
            (self.page_number == other.page_number and self.value < other.value)
        )

        if self_before:
            before, after = self, other
        else:
            before, after = other, self

        # on the same page
        if before.page_number == after.page_number:
            difference =  after.value - before.value
        else:
            before_part = before.page.height - before.value
            after_part = after.value
            page_diff_part = (after.page.page_number - before.page.page_number - 1) * before.page.height
            difference = before_part + after_part + page_diff_part
        
        if self_before:
            return -difference
        else:
            return difference

    def __add__(self, other: float | int) -> 'VerticalCoordinate':
        """
        Add a float value to the vertical coordinate.
        """
        return self.shift(other)
    
    
class HorizontalCoordinate(BaseModel):
    page: Any
    value: float

    @property
    def relative(self) -> float:
        return self.value / self.page.width

    @property
    def page_number(self) -> int:
        return self.page.page_number

    def __hash__(self):
        return hash((self.page_number, self.value))
    

    def __lt__(self, other):
        return self.value < other.value
    
    def __le__(self, other):
        return self.value <= other.value
    
    def __gt__(self, other):
        return self.value > other.value
    
    def __ge__(self, other):
        return self.value >= other.value
    
    def shift(self, delta: float | int) -> 'HorizontalCoordinate':
        if delta > 0:
            if self.value + delta <= self.page.width:
                return HorizontalCoordinate(page=self.page, value=self.value + delta)
            else:
                return HorizontalCoordinate(page=self.page, value=self.page.width)
        elif delta < 0:
            if self.value + delta >= 0:
                return HorizontalCoordinate(page=self.page, value=self.value + delta)
            else:
                return HorizontalCoordinate(page=self.page, value=0)
        else:
            return HorizontalCoordinate(page=self.page, value=self.value)

    def __sub__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return self.shift(-other)
        return self.value - other.value
    
    def __add__(self, other: float | int) -> 'HorizontalCoordinate':
        """
        Add a float value to the horizontal coordinate.
        """
        return self.shift(other)


class VerticalPosition(BaseModel):
    top: VerticalCoordinate
    bottom: VerticalCoordinate

    def __hash__(self):
        return hash((self.top, self.bottom))

    def __lt__(self, other):
        return self.bottom < other.top
    
    def __le__(self, other):
        return self.bottom <= other.top
    
    def __gt__(self, other):
        return self.top > other.bottom
    
    def __ge__(self, other):
        return self.top >= other.bottom

    def __sub__(self, other):
        if self.bottom < other.top:
            return self.bottom - other.top

        elif self.top > other.bottom:
            return self.top - other.bottom

        else:
            return 0
        

class HorizontalPosition(BaseModel):
    x0: HorizontalCoordinate
    x1: HorizontalCoordinate

    def __hash__(self):
        return hash((self.x0, self.x1))
    
    def __lt__(self, other):
        return self.x0 < other.x1
    
    def __le__(self, other):
        return self.x0 <= other.x1
    
    def __gt__(self, other):
        return self.x1 > other.x0
    
    def __ge__(self, other):
        return self.x1 >= other.x0
    
    def __sub__(self, other):
        
        if self.x1 < other.x0:
            return - (self.x1 - other.x0)

        elif self.x0 > other.x1:
            return self.x0 - self.x1

        else:
            return 0
    

class Position(BaseModel):
    x0: HorizontalCoordinate
    x1: HorizontalCoordinate
    top: VerticalCoordinate
    bottom: VerticalCoordinate

    def __hash__(self):
        return hash((self.x0, self.x1, self.top, self.bottom))

    def __eq__(self, other):
        return (
            self.x0 == other.x0 and
            self.x1 == other.x1 and
            self.top == other.top and
            self.bottom == other.bottom
        )
    
    @property
    def vertical(self) -> VerticalPosition:
        return VerticalPosition(top=self.top, bottom=self.bottom)

    @property
    def horizontal(self) -> HorizontalPosition:
        return HorizontalPosition(x0=self.x0, x1=self.x1)
    
    @property
    def crop(self) -> Crop:
        if self.vertical.top.page_number == self.vertical.bottom.page_number:
            return Crop(
                path=self.vertical.top.page.path,
                page_number=self.vertical.top.page_number,
                x0=self.x0.value,
                x1=self.x1.value,
                top=self.top.value,
                bottom=self.bottom.value
            )
        else:
            raise NotImplementedError("Crop not implemented for multiple pages")
        
    @property
    def show(self) -> None:
        """Display the position as a crop."""
        crop = self.crop
        crop.im.show()

    def contains(self, other: 'Position') -> bool:
        return (
            self.x0 <= other.x0 and
            self.x1 >= other.x1 and
            self.top <= other.top and
            self.bottom >= other.bottom
        )

    def __str__(self):
        return f"Position: ({self.x0}, {self.x1}, {self.top}, {self.bottom})"
    

def get_position(item: Any) -> Position:
    if isinstance(item, Position):
        return item
    elif hasattr(item, 'position'):
        return item.position
    else:
        raise ValueError(f"Item {item} does not have a position or is not a Position instance.")
    

def position_union(items: Iterable) -> Position:    
    min_x0 = min(get_position(item).horizontal.x0 for item in items)
    max_x1 = max(get_position(item).horizontal.x1 for item in items)
    min_top = min(get_position(item).vertical.top for item in items)
    max_bottom = max(get_position(item).vertical.bottom for item in items)

    return Position(x0=min_x0, x1=max_x1, top=min_top, bottom=max_bottom)


class PdfAnchor(BaseModel):
    """
    A base class for anchors in a PDF document.
    """
    @property
    def position(self) -> Position:
        """
        Get the position of the anchor.
        """
        raise NotImplementedError("Subclasses must implement the position property.")

    @property
    def page(self):
        return self.position.top.page
    
    @property
    def horizontal(self) -> HorizontalPosition:
        """
        Get the horizontal position of the anchor.
        """
        return self.position.horizontal

    @property
    def vertical(self) -> VerticalPosition:
        """
        Get the vertical position of the anchor.
        """
        return self.position.vertical

    @property
    def show(self):
        """
        Show this crop.
        """
        return self.position.crop.im.show

    def __hash__(self):
        try:
            self.position
        except NotImplementedError:
            return 0
        return hash(self.position)
    
    def __str__(self):
        return f"PdfAnchor(page: {self.position.top.page_number})"


def left_position_join(x: Iterable, y: Iterable, after: bool = True, uniquely: bool = True, keep_empty_x: bool = False, max_distance: int | None = None) -> Iterable[tuple]:
    """
    Bind two lists together based on their vertical positions.
    """
    x = sorted(x, key=lambda _: _.position.vertical)
    y = sorted(y, key=lambda _: _.position.vertical, reverse=after is False)

    for x_item in x:
        for y_item in y:
            if after:
                if max_distance:
                    if y_item.position.vertical - x_item.position.vertical > max_distance:
                        break # laters will be even further away
                
                if x_item.position.vertical < y_item.position.vertical:
                    if uniquely:
                        y.remove(y_item)
                    yield (x_item, y_item)
                    break

            else: 
                if max_distance:
                    if x_item.position.vertical - y_item.position.vertical > max_distance:
                        break # laters will be even further away

                if x_item.position.vertical > y_item.position.vertical:
                    if uniquely:
                        y.remove(y_item)
                    yield (x_item, y_item)
                    break
        else:
            if keep_empty_x:
                yield (x_item, None)
