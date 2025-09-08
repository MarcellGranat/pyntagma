from pathlib import Path

from pydantic import BaseModel
from pydantic_ai import NativeOutput

from src.pyntagma import Document
from src.pyntagma.agent import DocumentAgent, OllamaChatModel

# Create a document with the actual 2-part PDF files
test_files = [Path("tests/test_pdfs/test-1.pdf"), Path("tests/test_pdfs/test-2.pdf")]

doc = Document(files=test_files)


model = OllamaChatModel()
docagent = DocumentAgent(model=model, output_type=str, anchor=doc.pages[1].words[0])


def test_run():
    chat_ = docagent.run_sync("What is on the image?")
    assert isinstance(chat_.output, str)
    print(chat_)


class MetaData(BaseModel):
    text: str
    n_characters: int


def test_run_with_type_for_agent():
    docagent = DocumentAgent(
        model=model, output_type=NativeOutput(MetaData), anchor=doc.pages[1].words[0]
    )

    chat_ = docagent.run_sync("What is on the image? How many lettes does it contain?")
    output = MetaData.model_validate(chat_.output)
    assert isinstance(output.text, str)
    assert isinstance(output.n_characters, int)


def test_run_with_type_for_run():
    docagent = DocumentAgent(model=model, output_type=str, anchor=doc.pages[1].words[0])

    chat_ = docagent.run_sync(
        "What is on the image? How many lettes does it contain?", output_type=MetaData
    )
    output = MetaData.model_validate(chat_.output)
    assert isinstance(output.text, str)
    assert isinstance(output.n_characters, int)
    print(chat_)
