"""Agent utilities for reasoning over PDF anchors.

This module wires PydanticAI's `Agent` to work with Pyntagma PDF anchors,
optionally attaching cropped image bytes to prompts for multimodal models.
"""

from functools import partial
from typing import Any, Generic, Type, TypeVar

from pydantic import BaseModel, Field, PrivateAttr
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from .position import PdfAnchor, Position, get_binary_content

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

    def init_chat(self, anchor: PdfAnchor | Position, output_type: Any) -> "ImageChat":
        """Initialize a new chat session with this agent."""
        use_output_type = output_type or self.output_type
        return ImageChat(
            agent=self,
            anchor=anchor,
            output_type=use_output_type,
            message_history=[],
        )


T = TypeVar("T")
U = TypeVar("U")


class ImageChat(BaseModel, Generic[T]):
    """A chat session bound to an anchor with a statically-typed output.

    Using generics allows Pydantic (and type checkers) to know the type of
    `output` at class level: `ImageChat[MyModel]`.
    """

    agent: "DocumentAgent"
    anchor: PdfAnchor | Position
    output_type: Type[T] = Field(
        description="The expected output type from the agent (BaseModel or builtin).",
    )
    message_history: list = Field(
        default_factory=list, description="The message history of the chat."
    )
    output: T | None = Field(
        default=None, description="The latest output from the agent."
    )

    def prompt(
        self,
        user_prompt: str,
        include_anchor: bool | None = None,
    ) -> T:
        """Send a message to the agent, updating message history and output.

        The output is parsed to the instance's `output_type` and stored in
        `self.output`.
        """
        if include_anchor is None:
            include_anchor = len(self.message_history) == 0

        if include_anchor:
            binary_content = get_binary_content(self.anchor)
            user_prompt = [user_prompt, binary_content]  # type: ignore

        use_output_type: Type[T] = self.output_type

        agent_answer = self.agent.run_sync(
            user_prompt=user_prompt,
            message_history=self.message_history,
            output_type=use_output_type,
        )

        self.message_history = agent_answer.all_messages()
        if isinstance(use_output_type, type) and issubclass(use_output_type, BaseModel):
            self.output = use_output_type.model_validate(agent_answer.output)  # type: ignore[assignment]
        else:
            # For non-BaseModel outputs like `str` or `int`
            self.output = agent_answer.output  # type: ignore[assignment]

        return self.output  # type: ignore[return-value]

    def prompt_as(
        self, user_prompt: str, output_type: Type[U], include_anchor: bool | None = None
    ) -> U:
        """Run a single prompt and return a value parsed as `output_type`.

        Does not change this instance's declared `output_type` or `output` type.
        Useful when you want a different output type temporarily.
        """
        if include_anchor is None:
            include_anchor = len(self.message_history) == 0

        if include_anchor:
            binary_content = get_binary_content(self.anchor)
            user_prompt = [user_prompt, binary_content]  # type: ignore

        agent_answer = self.agent.run_sync(
            user_prompt=user_prompt,
            message_history=self.message_history,
            output_type=output_type,
        )

        self.message_history = agent_answer.all_messages()
        if isinstance(output_type, type) and issubclass(output_type, BaseModel):
            return output_type.model_validate(agent_answer.output)
        return agent_answer.output  # type: ignore[return-value]

    def change_type(self, output_type: Type[U]) -> "ImageChat[U]":
        """Return a new `ImageChat` instance sharing history but with new type.

        This pattern keeps `output` statically typed for Pydantic and type
        checkers while allowing type changes across turns.
        """
        return ImageChat[U](
            agent=self.agent,
            anchor=self.anchor,
            output_type=output_type,
            message_history=self.message_history,
        )
