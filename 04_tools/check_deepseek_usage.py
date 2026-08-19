"""Verify the DeepSeek connection and show what it cost."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deepseek_utils import DeepSeekClient, MODEL_PRO, MODEL_FLASH

print("Testing DeepSeek connection...\n")

try:
    client = DeepSeekClient()
except ValueError as e:
    print("[FAIL] " + str(e))
    sys.exit(1)

print("[OK]   API key loaded: " + client.api_key[:10] + "..." + client.api_key[-4:])

for model in (MODEL_FLASH, MODEL_PRO):
    try:
        reply = client.chat(
            "Reply with the single word: working",
            model=model,
            max_tokens=2000,
        )
        print("[OK]   " + model.ljust(18) + " -> " + reply.strip()[:40]
              + "   (" + str(client.last_usage.get("total_tokens", 0)) + " tokens)")
    except Exception as e:
        print("[FAIL] " + model.ljust(18) + " -> " + str(e)[:200])

print("\nSession total: " + str(client.session_tokens) + " tokens")
print("Dashboard: https://platform.deepseek.com/usage")
