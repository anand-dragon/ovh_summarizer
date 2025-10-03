import httpx
import logging
import trafilatura
import unicodedata

from app.core.config import MAX_SUMMARY_CHARS, OLLAMA_API

logger = logging.getLogger("app")


async def fetch_and_extract(url: str) -> str:
    """Fetch a webpage and extract cleaned text."""
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=20)
        r.raise_for_status()
        return trafilatura.extract(r.text) or ""


def _clean_summary(text: str) -> str:
    """Trim model boilerplate like “Here’s a summary …:” on the first line."""
    if not text:
        return ""

    # normalize unicode (e.g., ’ → '), then trim
    normalized = unicodedata.normalize("NFKC", text).replace("’", "'").strip()

    lines = normalized.splitlines()
    if not lines:
        return ""

    first = lines[0].strip()
    first_lower = first.lower()

    # common starts; we compare in lowercase
    prefixes = ("Here’s a summary of the text, under 1500 characters:\n\n",)

    # Drop the first line if it looks like a preface and ends with a colon
    drop = (any(first_lower.startswith(p) for p in prefixes) and first.endswith(":")) or (
        "summary" in first_lower and first.endswith(":")
    )

    if drop:
        logger.debug("[Ollama] Trimmed boilerplate first line: %r", first)
        cleaned = "\n".join(lines[1:]).lstrip()
    else:
        cleaned = normalized

    return cleaned


async def call_ollama(content: str) -> str:
    """Call Ollama with Gemma3:1B model and return summary."""
    prompt = (
        f"Summarize the following text in under {MAX_SUMMARY_CHARS} characters, "
        f"please skip the prefaces and just give raw summary:\n\n{content}"
    )

    async with httpx.AsyncClient(timeout=120) as client:
        logger.info(f"[Ollama] Sending request to {OLLAMA_API} with prompt length {len(prompt)}")
        resp = await client.post(
            OLLAMA_API,
            json={
                "model": "gemma3:1b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": MAX_SUMMARY_CHARS},
            },
        )
        resp.raise_for_status()
        data = resp.json()

        raw = (data.get("response", "") or "").strip()
        summary = _clean_summary(raw)[:MAX_SUMMARY_CHARS]
        return summary
