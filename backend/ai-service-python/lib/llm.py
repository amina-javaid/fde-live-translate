"""
lib/llm.py — the LLM translation call  (TODO: you implement)
============================================================
One job: turn an English string into Mexican Spanish using an LLM.

Provider is your choice. The default example below is Anthropic Claude
(`pip install anthropic`, set ANTHROPIC_API_KEY). Hamza's launched version
used Google Gemini — either is fine. Whatever you pick:

  - Write a PROMPT that pins the register to Mexican Spanish (es-MX), not
    generic/Castilian Spanish. Ask for ONLY the translation, no preamble.
  - Keep numbers, prices ($), and product/model codes unchanged.
  - Return a clean string (strip quotes/whitespace the model may add).

FAIL LOUD: do NOT wrap the call in a try/except that returns `text` on error.
If the provider fails, let the exception propagate so the caller returns a 502.
Silently returning the untranslated input is an automatic fail on this
assignment (and a real production bug — it ships English while looking healthy).
"""
import os

from openai import AsyncOpenAI

MODEL_DEFAULT = os.getenv("MODEL", "gpt-4o-mini")

# One shared async client (a connection pool) for the whole service. Created
# lazily on first use so the .env is already loaded by the time we build it.
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()  # reads OPENAI_API_KEY from the environment
    return _client


SYSTEM_PROMPT = (
    "You are a professional translator specializing in Mexican Spanish (es-MX). "
    "Translate the user's English text into natural, fluent Mexican Spanish as "
    "spoken in Mexico — not Castilian/European Spanish and not neutral 'Latin "
    "American' Spanish. Use Mexican vocabulary and register. Return ONLY the "
    "translation: no quotes, no explanations, no preamble, no alternatives. "
    "Preserve exactly, without translating: numbers, prices and currency symbols "
    "($), URLs, email addresses, and product/model codes (e.g. MB-120)."
)


async def translate_text(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT) -> str:
    """Return `text` translated into `target` (Mexican Spanish by default).

    Fails loud: any provider error propagates so the caller returns a 502.
    We never fall back to returning the untranslated English.
    """
    client = _get_client()
    resp = await client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return resp.choices[0].message.content.strip()
