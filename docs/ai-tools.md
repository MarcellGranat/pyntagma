# AI Tools

Pyntagma integrates neatly with multimodal LLM workflows via a small wrapper
around PydanticAI, enabling you to attach precise page crops to prompts.

## DocumentAgent

`DocumentAgent` (see `src/pyntagma/agent.py`) wraps a `pydantic_ai.Agent` and
optionally appends a PNG crop of a selected anchor to your user prompt.

Key points

- Works with any PydanticAI chat model (e.g., OpenAI-compatible, Ollama).
- `include_image=True` adds `BinaryContent` from `PdfAnchor.binary_content`.
- Supports typed outputs; wraps with `NativeOutput` for some backends.

Basic usage

```python
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from pyntagma import Document
from src.pyntagma.agent import DocumentAgent

doc = Document(files=["tests/test_pdfs/test-1.pdf"])  # sample
page = doc.pages[0]
anchor = page.lines[0]  # any PdfAnchor subclass with a .position

model = OpenAIChatModel(
    model_name="gemma3:4b",
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)

agent = DocumentAgent(anchor=anchor, model=model, output_type=str)
resp = agent.run_sync("Summarize this snippet", include_image=True)
print(resp.data)
```

Tips

- Use algebra (`position_union`, `left_position_join`) to craft precise crops
  before sending to the model.
- Keep crops tight; smaller, relevant images reduce token/compute costs.
- For local models via Ollama, ensure the server is running and reachable.
