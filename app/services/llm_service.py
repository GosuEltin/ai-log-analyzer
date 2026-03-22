import re
from openai import OpenAI
from app.core.config import settings

client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def translate_query_to_english(user_query: str) -> str:
    """Translate Vietnamese user query to English so the AI model understands it better."""
    if not user_query or not user_query.strip():
        return user_query

    # Quick check: if it looks like pure ASCII (English), skip translation
    non_ascii = sum(1 for c in user_query if ord(c) > 127)
    if non_ascii == 0:
        return user_query

    if not settings.GROQ_API_KEY:
        return user_query

    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a translator. Translate the following Vietnamese text to English. "
                        "Keep technical terms (like server names, error codes, ports) unchanged. "
                        "Only output the translated text, nothing else."
                    ),
                },
                {"role": "user", "content": user_query},
            ],
            temperature=0.1,
        )
        translated = response.choices[0].message.content.strip()
        return translated if translated else user_query
    except Exception:
        return user_query


def _clean_markdown(text: str) -> str:
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_diagnosis_lines(lines: list[str]) -> list[str]:
    cleaned = []
    blocked = {
        "primary issue:",
        "primary issue",
        "secondary issue:",
        "secondary issue",
        "certainty:",
        "certainty",
        "final diagnosis:",
        "final diagnosis",
    }

    for line in lines:
        line = _clean_markdown(line).strip()
        if not line:
            continue
        if line.lower() in blocked:
            continue
        cleaned.append(line)

    return cleaned


def generate_incident_summary(payload: dict) -> str:
    if not settings.GROQ_API_KEY:
        return (
            "Overview: Multiple errors detected, primarily in mod_jk/workerEnv module. "
            "Primary Issue: mod_jk workerEnv error state is the dominant cluster. "
            "Probable Cause: Backend unresponsive or AJP connection failure between server and app. "
            "Priority Action: Verify backend health, AJP port 8009, and mod_jk logs."
        )

    prompt = f"""
You are a senior Apache log analysis assistant with technical documentation support.

Analysis Data:
{payload}

Write a very short report in English, maximum 160 words.
Do not use markdown, tables, or bullets.
Respond strictly in these 4 lines:

Overview: ...
Primary Issue: ...
Probable Cause: ...
Priority Action: ...

Requirements:
- Adhere to user_query if provided.
- If requested to focus on backend/Tomcat/AJP, downgrade other issues to secondary.
- Use retrieved_knowledge when applicable.
- Do not fabricate information.
"""

    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": "Bạn là trợ lý phân tích log Apache."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()
        return _clean_markdown(text)
    except Exception as e:
        return f"Không gọi được mô hình AI. Lỗi: {str(e)}"


def generate_final_incident_report(payload: dict) -> tuple[str, list[str]]:
    if not settings.GROQ_API_KEY:
        final_summary = (
            "After high-priority checks, results strongly suggest the backend is unresponsive or the AJP connection "
            "between the web server and backend is failing."
        )
        final_diagnosis = [
            "Highly likely that backend/Tomcat is unresponsive or not listening on AJP port 8009.",
            "Mod_jk workerEnv and scoreboard errors are consistent with Apache being unable to connect.",
            "Directory access issues are secondary and not the focus of this incident.",
        ]
        return final_summary, final_diagnosis

    prompt = f"""
You are a senior backend incident investigation assistant.

Data after executing diagnostic tools:
{payload}

Reply in English using the following format and DO NOT use markdown:

FINAL_SUMMARY:
<a concise paragraph, maximum 120 words>

FINAL_DIAGNOSIS:
- <each line is a complete conclusion>
- <do not use headings like Primary Issue within the list>
- <do not use bold markdown>

Requirements:
- Adhere closely to user_query if provided.
- Incorporate tool_results to update conclusions.
- Distinguish between primary and secondary issues.
- Be cautious, avoid absolute assertions if evidence is insufficient.
- Use phrases like: "highly likely", "indicates", "supports the hypothesis".
- Do not fabricate info.
"""

    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a senior backend incident investigation assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = _clean_markdown(response.choices[0].message.content.strip())

        final_summary = ""
        final_diagnosis = []

        if "FINAL_SUMMARY:" in text:
            parts = text.split("FINAL_SUMMARY:", 1)[1]
            if "FINAL_DIAGNOSIS:" in parts:
                summary_part, diagnosis_part = parts.split("FINAL_DIAGNOSIS:", 1)
                final_summary = _clean_markdown(summary_part).strip()

                diagnosis_lines = []
                for line in diagnosis_part.splitlines():
                    line = line.strip()
                    if line.startswith("-"):
                        diagnosis_lines.append(line.lstrip("- ").strip())

                final_diagnosis = _clean_diagnosis_lines(diagnosis_lines)
            else:
                final_summary = _clean_markdown(parts).strip()

        if not final_summary:
            final_summary = text

        final_summary = _clean_markdown(final_summary)
        final_diagnosis = _clean_diagnosis_lines(final_diagnosis)

        return final_summary, final_diagnosis
    except Exception as e:
        return f"Không gọi được mô hình AI ở bước final reasoning. Lỗi: {str(e)}", []