"""Agent utilities for reasoning over PDF anchors.

This module wires PydanticAI's `Agent` to work with Pyntagma PDF anchors,
optionally attaching cropped image bytes to prompts for multimodal models.
"""

from functools import partial
from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from src.pyntagma.position import PdfAnchor

# Convenience factory for creating Ollama-backed chat models with defaults.
OllamaChatModel = partial(
    OpenAIChatModel,
    model_name="gemma3:4b",  # most prefered model
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)


class DocumentAgent(BaseModel):
    """Small wrapper around a PydanticAI `Agent` bound to a PDF anchor.

    - Attaches an anchor crop as `BinaryContent` to the first user prompt when
      `include_image=True` (default on first run), enabling multimodal context.
    - Allows specifying an `output_type` which is wrapped with `NativeOutput`
      for certain models (e.g. Gemma on Ollama) to keep parsing consistent.
    """

    anchor: PdfAnchor
    output_type: Any
    # Accept any chat model implementation (e.g., OpenAIChatModel)
    model: Any
    image_added: bool = False
    _agent: Agent | None = None  # initialised in `model_post_init`

    def model_post_init(self, _) -> None:
        """Create the underlying PydanticAI agent after model init."""
        self._agent = Agent(model=self.model, output_type=self.output_type)

    @property
    def anchor_content(self) -> Any:
        """Return the anchor's `BinaryContent` (PNG bytes of its crop)."""
        return self.anchor.binary_content

    def run_sync(
        self,
        user_prompt,
        anchor: PdfAnchor | None = None,
        output_type: Any = None,
        include_image: bool | None = None,
        **kwargs,
    ):
        """Run the agent synchronously with optional image context.

        - If `include_image` is True, append the anchor crop as BinaryContent to
          the prompt. When `anchor` is provided, that anchor is used; otherwise
          `self.anchor` is used.
        - `user_prompt` can be a string or a list of content items; the image is
          appended appropriately.
        """
        content = user_prompt
        if include_image is None:
            if self.image_added is True:
                include_image = False
            if self.image_added is False:
                include_image = True
                self.image_added = True
        if include_image:
            use_anchor = anchor or self.anchor
            if use_anchor is not None:
                if isinstance(content, (list, tuple)):
                    content = list(content) + [use_anchor.binary_content]
                else:
                    content = [content, use_anchor.binary_content]

        use_output_type = output_type or self.output_type

        if use_output_type is not None:
            if "gemma3" in self.model.model_name:
                use_output_type = NativeOutput(use_output_type)
        if self._agent is not None:
            return self._agent.run_sync(content, **kwargs)
        raise Exception("Agent is not created!")
