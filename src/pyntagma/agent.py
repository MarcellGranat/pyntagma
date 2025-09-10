"""Agent utilities for reasoning over PDF anchors.

This module wires PydanticAI's `Agent` to work with Pyntagma PDF anchors,
optionally attaching cropped image bytes to prompts for multimodal models.
"""

from functools import partial
from typing import Any, TypeVar

from pydantic import BaseModel, Field, PrivateAttr
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from .position import PdfAnchor, Position, get_binary_content, get_position

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

    model: Any
    output_type: Any = (
        str  # Accept any chat model implementation (e.g., OpenAIChatModel)
    )
    system_prompt: str = "You are a helpful assistant to extract data from historical archives. You try to be concise and accurate."
    _agent: Agent | None = PrivateAttr(default=None)  # initialised in `model_post_init`

    def model_post_init(self, _) -> None:
        """Create the underlying PydanticAI agent after model init."""
        output_type = self.output_type

        if self.output_type is not None and "gemma3" in self.model.model_name:
            if issubclass(self.output_type, BaseModel):
                output_type = NativeOutput(self.output_type)

        self._agent = Agent(
            model=self.model, output_type=output_type, system_prompt=self.system_prompt
        )  # type: ignore

    def run_sync(
        self,
        user_prompt,
        message_history: list | None = None,
        output_type: Any = None,
        **kwargs,
    ) -> Any:
        """Run the agent synchronously with optional image context.

        - If `include_image` is True, append the anchor crop as BinaryContent to
          the prompt. When `anchor` is provided, that anchor is used; otherwise
          `self.anchor` is used.
        - `user_prompt` can be a string or a list of content items; the image is
          appended appropriately.
        """
        if output_type is not None:
            if "gemma3" in self.model.model_name:
                output_type = NativeOutput(output_type)

        if self._agent is not None:
            return self._agent.run_sync(
                user_prompt=user_prompt,
                output_type=output_type,
                message_history=message_history,
                **kwargs,
            )
        raise Exception("Agent is not created!")


T = TypeVar("T")


class ImageChat(BaseModel):
    """A chat message with an optional image attachment."""

    agent: DocumentAgent
    anchor: PdfAnchor | Position
    output_type: Any = Field(
        default=str,
        description="The expected output type from the agent (by BaseModel).",
    )
    message_history: list = Field(
        default_factory=list, description="The message history of the chat."
    )
    output: Any = Field(default=None, description="The latest output from the agent.")

    def prompt(
        self,
        user_prompt: str,
        output_type: T = None,
        include_anchor: bool | None = None,
    ) -> T:
        """Send a message to the agent, updating message history and output."""
        if include_anchor is None:
            include_anchor = len(self.message_history) == 0

        if include_anchor:
            binary_content = get_binary_content(self.anchor)
            user_prompt = [user_prompt, binary_content]  # type: ignore

        use_output_type = output_type or self.output_type

        agent_answer = self.agent.run_sync(
            user_prompt=user_prompt,
            message_history=self.message_history,
            output_type=use_output_type,
        )

        self.message_history = agent_answer.all_messages()
        if issubclass(use_output_type, BaseModel):  # type: ignore
            self.output = use_output_type.model_validate(agent_answer.output)
        else:
            self.output = agent_answer.output

        return self.output
