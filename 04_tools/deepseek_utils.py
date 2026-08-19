"""
DeepSeek API wrapper for ISZE tasks.

Models available on this account (verified 19 Aug 2026):
  deepseek-v4-pro    - reasoning model. Slower, better at analysis. Burns
                       completion tokens on internal reasoning first, so
                       always give it a generous max_tokens (>= 1000).
  deepseek-v4-flash  - fast, cheap. Good for bulk/simple work.
                       (the alias "deepseek-chat" also maps to flash)

Usage:
    from deepseek_utils import DeepSeekClient
    client = DeepSeekClient()
    print(client.chat("Summarise this: ..."))
    print(client.last_usage)   # token counts for the call you just made
"""

import os
import requests
from typing import Optional, List, Dict

API_URL = "https://api.deepseek.com/chat/completions"

MODEL_PRO = "deepseek-v4-pro"
MODEL_FLASH = "deepseek-v4-flash"


def _load_env():
    """Load .env from the ISZE project root, wherever this file is called from."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in (
        os.path.join(os.path.dirname(here), ".env"),  # project root
        os.path.join(here, ".env"),                   # 04_tools/
        ".env",                                       # cwd
    ):
        if os.path.exists(candidate):
            load_dotenv(candidate)
            return


class DeepSeekClient:
    def __init__(self, api_key: Optional[str] = None, model: str = MODEL_PRO):
        _load_env()
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not found.\n"
                "Expected a .env file in the ISZE project root containing:\n"
                "  DEEPSEEK_API_KEY=sk-...\n"
                "The file must be plain UTF-8 (no BOM). PowerShell's '>' "
                "redirect writes UTF-16 and will NOT work."
            )
        self.model = model
        self.last_usage: Dict = {}
        self.session_tokens = 0

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: Optional[str] = None,
    ) -> str:
        """Send a prompt, return the reply text. Token usage lands in .last_usage."""
        messages: List[Dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        r = requests.post(API_URL, json=payload, headers={
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
        }, timeout=180)

        if r.status_code != 200:
            raise RuntimeError("DeepSeek API " + str(r.status_code) + ": " + r.text[:500])

        data = r.json()
        self.last_usage = data.get("usage", {})
        self.session_tokens += self.last_usage.get("total_tokens", 0)

        choice = data["choices"][0]
        content = choice["message"].get("content", "")

        if not content:
            # Reasoning model ran out of budget before writing an answer.
            if choice.get("finish_reason") == "length":
                raise RuntimeError(
                    "Model used its whole token budget on internal reasoning and "
                    "returned no answer. Raise max_tokens (try 2000+), or use "
                    "model=" + MODEL_FLASH + " for simple tasks."
                )
        return content

    def usage_report(self) -> str:
        """Human-readable summary of the last call."""
        u = self.last_usage
        if not u:
            return "No calls made yet."
        return (
            "Last call: " + str(u.get("prompt_tokens", 0)) + " in + "
            + str(u.get("completion_tokens", 0)) + " out = "
            + str(u.get("total_tokens", 0)) + " tokens"
            + "  |  session total: " + str(self.session_tokens)
        )

    # --- convenience wrappers ---

    def analyze(self, data: str, task: str, **kw) -> str:
        return self.chat("Task: " + task + "\n\nData:\n" + data, **kw)

    def report(self, topic: str, data: str, fmt: str = "markdown", **kw) -> str:
        return self.chat(
            "Topic: " + topic + "\n\nData:\n" + data,
            system_prompt="You are a professional analyst. Produce a " + fmt + " report.",
            **kw
        )
