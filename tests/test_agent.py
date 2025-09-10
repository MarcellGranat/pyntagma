import json
import socket
import subprocess
from pathlib import Path
from shutil import which

import pytest
from pydantic import BaseModel, Field

from src.pyntagma import Document
from src.pyntagma.agent import DocumentAgent, ImageChat, OllamaChatModel


def _ollama_model_available(model_name: str = "gemma3:4b") -> bool:
    """Return True if Ollama is reachable and the model is present.

    Checks in this order:
    - If `ollama` CLI exists, use `ollama list` to find the model.
    - Otherwise, try the local HTTP API `http://127.0.0.1:11434/api/tags`.
    """
    # 1) Prefer the CLI if available
    if which("ollama") is not None:
        try:
            res = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=5
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    # Output columns typically start with the model name
                    first = line.split()[0] if line.split() else ""
                    if model_name in first:
                        return True
        except Exception:
            pass

    # 2) Fallback to local API probe
    try:
        # Quick TCP reachability check before HTTP
        with socket.create_connection(("127.0.0.1", 11434), timeout=2):
            pass
    except OSError:
        return False

    try:
        # Use stdlib to avoid external deps
        import urllib.request

        with urllib.request.urlopen(
            "http://127.0.0.1:11434/api/tags", timeout=3
        ) as resp:
            body = resp.read()
        data = json.loads(body.decode("utf-8"))
        models = data.get("models", [])
        for m in models:
            name = m.get("model", "")
            if model_name in name:
                return True
    except Exception:
        return False

    return False


# Skip the entire module if Ollama or the required model is not available
pytestmark = pytest.mark.skipif(
    not _ollama_model_available(), reason="Requires Ollama with model gemma3:4b"
)

# Create a document with the actual 2-part PDF files
test_files = [Path("tests/test_pdfs/test-1.pdf"), Path("tests/test_pdfs/test-2.pdf")]

doc = Document(files=test_files)


model = OllamaChatModel()


def test_str_output():
    docagent = DocumentAgent(
        model=model, system_prompt_attachment=doc.pages[1].words[0]
    )
    chat_ = docagent.run_sync("What is on the image?")
    assert isinstance(chat_.output, str)
    print(chat_)


class MetaData(BaseModel):
    text: str
    n_characters: int


word = doc.pages[1].words[0]


def test_run_with_type_for_agent():
    docagent = DocumentAgent(
        model=model,
        output_type=MetaData,
    )

    chat_ = docagent.run_sync(
        ["What is on the image? How many lettes does it contain?", word.binary_content]
    )
    output = MetaData.model_validate(chat_.output)
    assert isinstance(output.text, str)
    assert isinstance(output.n_characters, int)


def test_run_with_type_for_run():
    docagent = DocumentAgent(model=model, output_type=str)

    chat_ = docagent.run_sync(
        ["What is on the image? How many lettes does it contain?", word.binary_content],
        output_type=MetaData,
    )
    output = MetaData.model_validate(chat_.output)
    print(output)
    assert isinstance(output.text, str)
    assert isinstance(output.n_characters, int)


def test_run_multiple():
    class ImageWord(BaseModel):
        word: str = Field(description="The word on the image")
        n_letters: int = Field(description="The number of letters in the word")

    docagent = DocumentAgent(
        model=model,
        output_type=ImageWord,
    )

    chat1 = docagent.run_sync(
        [
            "What is the word on the image? How many lettes does it contain?",
            word.binary_content,
        ]
    )
    assert isinstance(chat1.output.word, str)
    print(chat1)

    class Letters(BaseModel):
        first_letter: str
        last_letter: str

    chat2 = docagent.run_sync(
        "Now, tell me the first and last letter of the word from the image.",
        output_type=Letters,
        message_history=chat1.all_messages(),
    )

    assert chat2.output.first_letter == chat1.output.word[0]
    assert chat2.output.last_letter in ["s", "-"]  # might fail sometimes "-"
    print(chat2)


docagent = DocumentAgent(model=model)


def test_chat():
    chat = ImageChat(agent=docagent, anchor=word, output_type=str)

    chat.prompt("What is on the image?")
    assert isinstance(chat.output, str)

    class Letters(BaseModel):
        n: int = Field(description="The number of letters in the word")

    result = chat.prompt_as("How many letters does it contain?", output_type=Letters)

    assert isinstance(result.n, int)
    assert 6 < result.n < 10

    class WordMeta(BaseModel):
        word: str = Field(description="The word on the image")

    class LetterMeta(BaseModel):
        letter: str = Field(description="The first letter of the word")

    result2 = chat.prompt_as(
        "What is the word on the image?", output_type=WordMeta | LetterMeta
    )
    assert isinstance(result2.word, str)

    result3 = chat.prompt_as(
        "What is the first letter of the word?", output_type=WordMeta | LetterMeta
    )
    assert result3.letter == result2.word[0]
