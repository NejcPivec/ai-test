"""Safety checks for user messages and generated assistant answers."""

import re

import ollama

from model_config import GUARD_MODEL


GUARD_SYSTEM_PROMPT = """You are the safety classifier for the VAC chatbot.
Classify the supplied text for the general harm category.
Return exactly one word: Yes or No.
Return Yes when risk is detected and No when the text is safe.
Mark text UNSAFE when it requests or contains instructions for violence,
sexual exploitation, serious wrongdoing, malware, credential theft, or other
dangerous illegal activity. Ordinary archive, product, portal, and research
questions are SAFE.
"""

GUARD_BLOCK_MESSAGE = (
    "Na to vprašanje ne morem odgovoriti. Prosim, zastavi varno vprašanje, "
    "povezano z VAČ, virtualnimi razstavami, tektoniko ali uporabo portala."
)


class GuardUnavailableError(RuntimeError):
    """The configured Guardian model could not provide a decision."""


class UnsafeContentError(ValueError):
    """The Guardian model classified text as unsafe."""


def _parse_guard_decision(content: str) -> bool:
    """Return True for a safe No decision and reject ambiguity."""
    first_word = re.match(r"\s*([A-Za-z]+)", content or "")
    if not first_word:
        raise ValueError("Guardian returned no decision")

    decision = first_word.group(1).upper()
    if decision == "NO":
        return True
    if decision == "YES":
        return False
    raise ValueError(f"Guardian returned an unknown decision: {decision}")


def is_safe(text: str, stage: str) -> bool:
    """Ask Guardian for a safety decision and fail closed on uncertainty."""
    try:
        response = ollama.chat(
            model=GUARD_MODEL,
            messages=[
                {"role": "system", "content": GUARD_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            options={"temperature": 0},
        )
        decision = _parse_guard_decision(response["message"]["content"])
        print(f"Guardian: model={GUARD_MODEL} stage={stage} safe={decision}")
        return decision
    except (KeyError, TypeError, ValueError) as exc:
        raise GuardUnavailableError(f"Guardian returned an invalid decision: {exc}") from exc
    except Exception as exc:
        raise GuardUnavailableError(f"Guardian request failed: {exc}") from exc


def assert_safe(text: str, stage: str) -> None:
    if not is_safe(text, stage):
        raise UnsafeContentError(f"Guardian blocked {stage} content")
