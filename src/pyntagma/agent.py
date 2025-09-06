from functools import partial
from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from src.pyntagma.position import PdfAnchor

ollama_model = OpenAIChatModel(
    model_name="gemma3:4b",
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)

OllamaChatModel = partial(
    OpenAIChatModel,
    model_name="gemma3:4b",  # most prefered model
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)


class DocumentAgent(BaseModel):
    anchor: PdfAnchor
    output_type: Any
    # Accept any chat model implementation (e.g., OpenAIChatModel)
    model: Any
    image_added: bool = False
    _agent: Agent | None = None  # initalise later

    def model_post_init(self, _) -> None:
        self._agent = Agent(model=self.model, output_type=self.output_type)

    @property
    def anchor_content(self):
        # Reuse the anchor's own binary content (PNG bytes of its crop)
        return self.anchor.binary_content

    def run_sync(
        self,
        user_prompt,
        anchor: PdfAnchor | None = None,
        output_type: Any = None,
        include_image: bool | None = None,
        **kwargs,
    ):
        """
        Run the agent synchronously.

        - If `include_image` is True, append the anchor's image as BinaryContent
          to the user prompt. If `anchor` is provided, use that, otherwise fall
          back to `self.anchor`.
        - `user_prompt` can be a string or a list of content items; the image
          will be appended appropriately.
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
        if output_type is not None:
            if "gemma3" in self.model.model_name:
                output_type = NativeOutput(output_type)
        if self._agent is not None:
            return self._agent.run_sync(content, **kwargs)
        raise Exception("Agent is not created!")
