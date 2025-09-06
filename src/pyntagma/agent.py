from collections.abc import Sequence
from functools import partial

from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent, NativeOutput
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from src.pyntagma.pdf_reader import Crop


class Fruit(BaseModel):
    name: str
    color: str


class Vehicle(BaseModel):
    name: str
    wheels: int


ollama_model = OpenAIChatModel(
    model_name="gemma3:4b",
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)

OllamaChatModel = partial(
    OpenAIChatModel,
    model_name="gemma3:4b",  # most prefered model
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)


class DocumentAgent(Agent):
    """
    Agent that works on crops of your document.
    """

    def run_sync(
        self,
        user_prompt: str | Sequence | None = None,
        crop: Crop | None = None,
        **kwargs,
    ):
        if user_prompt is None and crop is not None:
            user_prompt = []

        if crop is not None:
            if isinstance(user_prompt, str):
                user_prompt = [user_prompt]

            crop_bytes = BinaryContent(crop.bytes, media_type="image/png")
            if not isinstance(user_prompt, list):
                raise TypeError("user_prompt is expected to be a list!")
            user_prompt.append(crop_bytes)

        super().run_sync(user_prompt=user_prompt, **kwargs)
