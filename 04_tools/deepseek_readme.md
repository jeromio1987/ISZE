# DeepSeek for ISZE

Verified working 19 Aug 2026. Key lives in `.env` at the project root.

## Run it

From the ISZE project root, **in PowerShell** (not inside a `>>>` Python prompt):

```powershell
python 04_tools/check_deepseek_usage.py      # connection test
python 04_tools/deepseek_examples.py 1       # summarise (flash)
python 04_tools/deepseek_examples.py 2       # pricing analysis (pro)
python 04_tools/deepseek_examples.py 3       # batch distributor review (pro)
```

If your prompt shows `>>>` you are inside Python. Type `exit()` first.

## Models on this account

| Model | Use for | Note |
|---|---|---|
| `deepseek-v4-pro` | analysis, judgement, anything you'd otherwise ask Claude | Reasoning model. Spends tokens thinking before answering — give it `max_tokens >= 2000` or it returns empty. |
| `deepseek-v4-flash` | summarising, extraction, bulk/repetitive work | Fast and cheap. Default to this for volume. |

`deepseek-chat` is an alias that resolves to flash.

## Use in your own scripts

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "04_tools"))
from deepseek_utils import DeepSeekClient, MODEL_PRO, MODEL_FLASH

client = DeepSeekClient()                      # defaults to pro
print(client.chat("your prompt", model=MODEL_FLASH))
print(client.usage_report())                   # tokens for that call
```

## Checking usage

Two ways:

1. **Per call, immediately** — every response carries its token count:
   `client.last_usage` -> `{'prompt_tokens': .., 'completion_tokens': .., 'total_tokens': ..}`
   or `client.usage_report()` for a one-line summary. `client.session_tokens`
   accumulates across the run.

2. **Account level** — https://platform.deepseek.com/usage, and the
   "API Key Usage" button on the API keys page. The key's "Last used"
   column updates once calls start landing.

## The .env file

Must be **plain UTF-8, no BOM**. This matters:

PowerShell's `>` redirect and `Out-File` write **UTF-16**, which python-dotenv
cannot read — it fails with `UnicodeDecodeError: invalid start byte 0xff`.
If you need to recreate the file, use Notepad (Save as, Encoding: UTF-8) or:

```powershell
[IO.File]::WriteAllText("$PWD\.env", "DEEPSEEK_API_KEY=sk-...`n")
```

`.env` is gitignored. The key is not in any tracked file.

## When to use DeepSeek vs Claude

- **DeepSeek** — volume work where the output is mechanical: summarising many
  documents, extracting fields, first-pass classification, batch formatting.
- **Claude (Cowork)** — anything where being wrong is expensive: pricing
  positions, IML/ITUK correspondence, sparring, work that touches the
  Kosha or dispute files.
