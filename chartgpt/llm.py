import os
import re
from typing import Any, Dict

import openai

from .constants import END_CODE_TAG, START_CODE_TAG


class LLM:
    """LLM class for generating code from a prompt.

    Args:
        model_name (str, optional): Model name. Defaults to "text-davinci-003".
        temperature (int, optional): Temperature. Defaults to 0.2.
        max_tokens (int, optional): Max tokens. Defaults to 1000.
        top_p (int, optional): Top p. Defaults to 1.
        frequency_penalty (int, optional): Frequency penalty. Defaults to 0.
        presence_penalty (int, optional): Presence penalty. Defaults to 0.
        api_key (str, optional): OpenAI API key. Defaults to None.

    Raises:
        ValueError: If no API key is provided.

    Returns:
        str: Generated code
    """

    def __init__(
        self,
        model_name: str = None,
        temperature: int = 0.2,
        max_tokens: int = 1000,
        top_p: int = 1,
        frequency_penalty: int = 0,
        presence_penalty: int = 0,
        chat: bool = True,
        api_key: str = None,
    ):
        self.model_name = model_name or "gpt-3.5-turbo" if chat else "text-davinci-003"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.chat = chat

        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or None
        if self.api_key is None:
            raise ValueError("Please provide an OpenAI API key")
        openai.api_key = self.api_key

        self.messages = []

    def _extract_code(self, response: str, separator: str = "```") -> str:
        """
        Extract the code from the response.

        Args:
            response (str): Response
            separator (str, optional): Separator. Defaults to "```".

        Returns:
            str: Extracted code from the response
        """
        code = response
        match = re.search(
            rf"{START_CODE_TAG}(.*)({END_CODE_TAG}|{END_CODE_TAG.replace('<', '</')})",
            code,
            re.DOTALL,
        )
        if match:
            code = match.group(1).strip()
        if len(code.split(separator)) > 1:
            code = code.split(separator)[1]

        if self.chat:
            code = code.replace("python", "")

        if "fig.show()" in code:
            code = code.replace("fig.show()", "fig")

        return code

    def generate_code(self, instructions: str) -> str:
        """
        Generate the code based on the instruction and the given prompt.

        Returns:
            str: Code
        """
        if self.chat:
            return self._extract_code(self.chat_completion(instructions))
        else:
            return self._extract_code(self.completion(instructions))

    @property
    def _default_params(self) -> Dict[str, Any]:
        """
        Get the default parameters for calling OpenAI API

        Returns (Dict): A dict of OpenAi API parameters

        """

        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }

    def completion(self, prompt: str) -> str:
        """
        Query the completion API

        Args:
            prompt (str): Prompt

        Returns:
            str: LLM response
        """
        params = {**self._default_params, "prompt": prompt}

        response = openai.Completion.create(**params)

        return response["choices"][0]["text"]

    def chat_completion(self, value: str) -> str:
        """
        Query the chat completion API

        Args:
            value (str): Prompt

        Returns:
            str: LLM response
        """
        params = {
            **self._default_params,
            "messages": [
                {
                    "role": "system",
                    "content": value,
                }
            ],
        }

        response = openai.ChatCompletion.create(**params)
        message = response["choices"][0]["message"]["content"]

        self.add_history(value, message)
        return message

    def add_history(self, user_message, bot_message):
        self.messages.append({"role": "system", "content": bot_message})
        self.messages.append({"role": "human", "content": user_message})
        return None
