# Algebra vs. Bidirectional Navigation

Pyntagma offers two complementary ways to work with documents:

- Algebra on positions: operate on geometric regions precisely and compose rules.
- Bidirectional navigation: move between text units (lines, words, chars) reliably.

Understanding the difference helps you design robust extraction pipelines.

## Algebra: Geometry First

The algebra treats regions as first-class values.

- Coordinates: `VerticalCoordinate`, `HorizontalCoordinate`
- Spans: `VerticalPosition`, `HorizontalPosition`
- Region: `Position` (x0, x1, top, bottom)
- Set ops: `position_union(items)` returns the minimal bounding region.
- Joins: `left_position_join(x, y, after=True, uniquely=True, ...)` pairs items
  by relative vertical order with optional distance constraints.

Why it’s powerful

- Composable and testable: build extraction by combining small geometric rules.
- Deterministic: comparisons/orderings make behavior explicit across pages.
- Model-agnostic: works without OCR or AI; pairs well with both.

Example

```python
# Select a headline region then expand by padding logic
pos = position_union(page.lines[:2])
headline = Position(x0=pos.x0, x1=pos.x1, top=pos.top, bottom=pos.bottom)
im = headline.plot_on_page()
```

## Bidirectional Navigation: Structure First

Navigation makes it easy to traverse textual structure while staying grounded in geometry.

- From a `Line` → `words`: `line.words` or `words_of_line(line)`
- From a `Word` → `line`: `word.line` or `line_of_word(word)`
- From a `Word` → `chars`: `word.chars` or `chars_of_word(word)`
- From a `Char` → `word`: `char.word` or `word_of_char(char)`

Why it’s powerful

- Expressive: grab neighboring units without recomputing geometry.
- Symmetric: go up and down the hierarchy reliably.
- Efficient: many lookups are cached for repeated access patterns.

Example

```python
first = page.lines[0]
tokens = [w.text for w in first.words]
owner = first.words[0].line  # round-trip is safe
```

## Choosing the Right Tool or COMBINE

Most of the time, you’ll use both approaches together. Some examples:

You want the numbers from a page that is in the header:

```python
possible_words = [w.vertical.bottom.value < 100 for w in page.words]
numbers = [w for w in page.words if w.text.isdigit() and possible_words]
```


