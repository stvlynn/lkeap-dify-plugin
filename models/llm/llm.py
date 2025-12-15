import logging
from collections.abc import Generator
from typing import Optional, Union

from dify_plugin.entities.model.llm import LLMResult, LLMResultChunk, LLMResultChunkDelta, LLMUsage
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageContentType,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from dify_plugin.errors.model import CredentialsValidateFailedError, InvokeError
from dify_plugin.interfaces.model.large_language_model import LargeLanguageModel
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)


class LkeapLargeLanguageModel(LargeLanguageModel):
    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> LLMResult | Generator:
        """Invoke large language model"""
        client = self._setup_openai_client(credentials)

        # Convert messages to OpenAI format
        messages = self._convert_prompt_messages_to_dicts(prompt_messages)

        # Prepare parameters
        params = {
            "model": model,
            "messages": messages,
            "temperature": model_parameters.get("temperature", 0.6),
            "top_p": model_parameters.get("top_p", 0.6),
            "max_tokens": model_parameters.get("max_tokens", 4096),
            "stream": stream,
        }

        # Add optional parameters
        if stop:
            params["stop"] = stop
        if user:
            params["user"] = user

        # Add tools for function calling (only for V3 models)
        if tools and "v3" in model.lower():
            params["tools"] = [self._convert_tool_to_openai_format(tool) for tool in tools]

        # Add presence_penalty and frequency_penalty for V3.1-Terminus
        if "terminus" in model.lower():
            if "presence_penalty" in model_parameters:
                params["presence_penalty"] = model_parameters["presence_penalty"]
            if "frequency_penalty" in model_parameters:
                params["frequency_penalty"] = model_parameters["frequency_penalty"]

        try:
            response = client.chat.completions.create(**params)

            if stream:
                return self._handle_stream_response(model, credentials, prompt_messages, response)
            else:
                return self._handle_sync_response(model, credentials, prompt_messages, response)

        except Exception as e:
            raise InvokeError(f"Failed to invoke model: {str(e)}")

    def _setup_openai_client(self, credentials: dict) -> OpenAI:
        """Setup OpenAI client with LKEAP credentials"""
        secret_key = credentials.get("secret_key")
        if not secret_key:
            raise CredentialsValidateFailedError("Secret Key is required")

        return OpenAI(
            api_key=secret_key,
            base_url="https://api.lkeap.tencentcloud.com/v1"
        )

    def _convert_prompt_messages_to_dicts(self, prompt_messages: list[PromptMessage]) -> list[dict]:
        """Convert Dify PromptMessage to OpenAI message format"""
        messages = []
        for message in prompt_messages:
            if isinstance(message, SystemPromptMessage):
                messages.append({"role": "system", "content": message.content})
            elif isinstance(message, UserPromptMessage):
                if isinstance(message.content, str):
                    messages.append({"role": "user", "content": message.content})
                else:
                    # Handle multimodal content
                    content = []
                    for item in message.content:
                        if item.type == PromptMessageContentType.TEXT:
                            content.append({"type": "text", "text": item.data})
                        elif item.type == PromptMessageContentType.IMAGE:
                            content.append({
                                "type": "image_url",
                                "image_url": {"url": item.data}
                            })
                    messages.append({"role": "user", "content": content})
            elif isinstance(message, AssistantPromptMessage):
                msg = {"role": "assistant", "content": message.content or ""}
                if message.tool_calls:
                    msg["tool_calls"] = [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in message.tool_calls
                    ]
                messages.append(msg)
            elif isinstance(message, ToolPromptMessage):
                messages.append({
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content
                })
        return messages

    def _convert_tool_to_openai_format(self, tool: PromptMessageTool) -> dict:
        """Convert Dify tool to OpenAI tool format"""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        }

    def _handle_sync_response(
        self, model: str, credentials: dict, prompt_messages: list[PromptMessage], response
    ) -> LLMResult:
        """Handle synchronous response"""
        choice = response.choices[0]
        message = choice.message

        # Create assistant message
        assistant_message = AssistantPromptMessage(content=message.content or "")

        # Handle tool calls
        if hasattr(message, "tool_calls") and message.tool_calls:
            assistant_message.tool_calls = []
            for tool_call in message.tool_calls:
                assistant_message.tool_calls.append(
                    AssistantPromptMessage.ToolCall(
                        id=tool_call.id,
                        type=tool_call.type,
                        function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments
                        )
                    )
                )

        # Calculate usage
        usage = self._calc_response_usage(
            model, credentials, response.usage.prompt_tokens, response.usage.completion_tokens
        )

        return LLMResult(
            model=model,
            prompt_messages=prompt_messages,
            message=assistant_message,
            usage=usage
        )

    def _handle_stream_response(
        self, model: str, credentials: dict, prompt_messages: list[PromptMessage], response
    ) -> Generator:
        """Handle streaming response"""
        full_content = ""
        full_reasoning = ""
        is_reasoning = False
        tool_calls_buffer = []

        for index, chunk in enumerate(response):
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            # Handle reasoning content (for R1 models)
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                if not is_reasoning:
                    full_content += "<think>\n"
                    is_reasoning = True
                full_reasoning += delta.reasoning_content
                full_content += delta.reasoning_content

                yield LLMResultChunk(
                    model=model,
                    prompt_messages=prompt_messages,
                    delta=LLMResultChunkDelta(
                        index=index,
                        message=AssistantPromptMessage(content=delta.reasoning_content)
                    )
                )

            # Handle regular content
            if hasattr(delta, "content") and delta.content:
                if is_reasoning:
                    full_content += "\n</think>"
                    is_reasoning = False
                full_content += delta.content

                yield LLMResultChunk(
                    model=model,
                    prompt_messages=prompt_messages,
                    delta=LLMResultChunkDelta(
                        index=index,
                        message=AssistantPromptMessage(content=delta.content)
                    )
                )

            # Handle tool calls
            if hasattr(delta, "tool_calls") and delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    # Buffer tool calls
                    if tool_call_delta.index >= len(tool_calls_buffer):
                        tool_calls_buffer.append({
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        })

                    if tool_call_delta.id:
                        tool_calls_buffer[tool_call_delta.index]["id"] = tool_call_delta.id
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            tool_calls_buffer[tool_call_delta.index]["function"]["name"] += tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            tool_calls_buffer[tool_call_delta.index]["function"]["arguments"] += tool_call_delta.function.arguments

            # Handle finish
            if finish_reason:
                assistant_message = AssistantPromptMessage(content=full_content)

                # Add tool calls if present
                if tool_calls_buffer:
                    assistant_message.tool_calls = []
                    for tc in tool_calls_buffer:
                        assistant_message.tool_calls.append(
                            AssistantPromptMessage.ToolCall(
                                id=tc["id"],
                                type=tc["type"],
                                function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                                    name=tc["function"]["name"],
                                    arguments=tc["function"]["arguments"]
                                )
                            )
                        )

                # Get usage from final chunk
                usage = None
                if hasattr(chunk, "usage") and chunk.usage:
                    usage = self._calc_response_usage(
                        model, credentials, chunk.usage.prompt_tokens, chunk.usage.completion_tokens
                    )

                yield LLMResultChunk(
                    model=model,
                    prompt_messages=prompt_messages,
                    delta=LLMResultChunkDelta(
                        index=index,
                        message=assistant_message,
                        finish_reason=finish_reason,
                        usage=usage
                    )
                )

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """Validate credentials"""
        try:
            client = self._setup_openai_client(credentials)
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                stream=False
            )
        except Exception as e:
            raise CredentialsValidateFailedError(f"Credentials validation failed: {str(e)}")

    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
    ) -> int:
        """Get number of tokens for given prompt messages"""
        if len(prompt_messages) == 0:
            return 0
        prompt = self._convert_messages_to_prompt(prompt_messages)
        return self._get_num_tokens_by_gpt2(prompt)

    def _convert_messages_to_prompt(self, messages: list[PromptMessage]) -> str:
        """Convert messages to a single prompt string for token counting"""
        text = ""
        for message in messages:
            if isinstance(message, SystemPromptMessage):
                text += f"System: {message.content}\n"
            elif isinstance(message, UserPromptMessage):
                if isinstance(message.content, str):
                    text += f"User: {message.content}\n"
                else:
                    for item in message.content:
                        if item.type == PromptMessageContentType.TEXT:
                            text += f"User: {item.data}\n"
            elif isinstance(message, AssistantPromptMessage):
                text += f"Assistant: {message.content}\n"
            elif isinstance(message, ToolPromptMessage):
                text += f"Tool: {message.content}\n"
        return text.rstrip()

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        """Map model invoke error to unified error"""
        return {
            InvokeError: [OpenAIError]
        }
