import re
import ollama
from prompts import PROMPT_KU, PROMPT_NU
from model_config import ANSWER_MODEL

CHAT_MODEL = ANSWER_MODEL



def build_system_prompt(template: str, context: str, route: dict | None) -> str:
    safe_context = context if context else "(Ni relevantnega konteksta.)"
    route = route or {}

    if "{intent}" in template or "{corpus}" in template or "{current_page}" in template:
        return template.format(
            intent=route.get("intent", "faq"),
            corpus=route.get("corpus", "docs"),
            current_page=route.get("current_page", "-"),
            context=safe_context
        )

    return template.format(context=safe_context)


def contains_non_vac_url(text: str) -> bool:
    urls = re.findall(r"https?://\S+", text)
    for url in urls:
        if "vac.sjas.gov.si" not in url:
            return True
    return False


async def ask_ollama(
    message: str,
    user_type: str,
    route: dict | None = None,
    context: str = "",
    history: list | None = None
) -> str:
    history = history or []

    template = PROMPT_NU if user_type == "NU" else PROMPT_KU
    system = build_system_prompt(template, context, route)

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    print(
        f"🤖 MODEL: {CHAT_MODEL} | tip={user_type} | "
        f"intent={(route or {}).get('intent')} | "
        f"corpus={(route or {}).get('corpus')} | "
        f"kontekst={len(context)} znakov"
    )

    response = ollama.chat(
        model=ANSWER_MODEL,
        messages=messages,
        options={
            "temperature": 0.1,
            "top_p": 0.9,
        }
    )

    answer = response["message"]["content"].strip()

    if route and route.get("intent") == "search":
        if contains_non_vac_url(answer):
            return (
                "Za iskano gradivo trenutno nisem našel dovolj relevantnih zadetkov v VAČ. "
                "Poskusi z bolj natančnim pojmom, letnico, krajem ali signaturo."
            )

    return answer
