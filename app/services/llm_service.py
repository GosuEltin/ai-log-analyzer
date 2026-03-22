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
        "issue chính:",
        "issue chính",
        "issue phụ:",
        "issue phụ",
        "issue phu:",
        "issue phu",
        "chắc chắn:",
        "chắc chắn",
        "mức độ chắc chắn:",
        "mức độ chắc chắn",
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
            "Tổng quan: Hệ thống ghi nhận nhiều lỗi, chủ yếu ở mod_jk/workerEnv. "
            "Lỗi chính: mod_jk workerEnv error state là cụm lỗi chi phối. "
            "Nguyên nhân khả dĩ: backend không phản hồi hoặc kết nối Apache tới backend qua AJP bị lỗi. "
            "Hành động ưu tiên: kiểm tra backend, AJP port và mod_jk.log trước, rồi mới rà cấu hình."
        )

    prompt = f"""
Bạn là trợ lý phân tích log Apache có hỗ trợ tài liệu kỹ thuật.

Dữ liệu phân tích:
{payload}

Hãy viết báo cáo cực ngắn bằng tiếng Việt, tối đa 160 từ.
Không dùng markdown, không dùng bảng, không dùng bullet.
Chỉ trả lời đúng 4 dòng theo mẫu này:

Tổng quan: ...
Lỗi chính: ...
Nguyên nhân khả dĩ: ...
Hành động ưu tiên: ...

Yêu cầu:
- Phải bám sát user_query nếu có
- Nếu user_query yêu cầu chỉ tập trung vào backend/Tomcat/AJP, hãy hạ mọi issue khác xuống mức issue phụ
- Nếu một issue xuất hiện ít hơn rõ rệt so với issue chính, chỉ mô tả nó là issue phụ
- Ưu tiên issue chính theo tần suất và mức độ ảnh hưởng
- Nếu có mod_jk workerEnv error state, phải ưu tiên backend/Tomcat, kết nối Apache -> backend, AJP port, rồi mới tới config
- Ưu tiên dùng retrieved_knowledge khi liên quan
- Không bịa thông tin
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
            "Sau khi chạy các kiểm tra ưu tiên cao, hệ thống nghi ngờ mạnh rằng backend không phản hồi hoặc kết nối AJP "
            "giữa Apache và backend đang lỗi; lỗi truy cập thư mục chỉ là issue phụ."
        )
        final_diagnosis = [
            "Nhiều khả năng backend/Tomcat không phản hồi hoặc chưa lắng nghe trên cổng AJP 8009.",
            "Các lỗi mod_jk workerEnv và scoreboard phù hợp với tình huống Apache không kết nối được tới backend.",
            "Issue truy cập thư mục là vấn đề phụ và không phải trọng tâm của điều tra này.",
        ]
        return final_summary, final_diagnosis

    prompt = f"""
Bạn là trợ lý điều tra sự cố backend.

Dữ liệu sau khi đã chạy tool:
{payload}

Hãy trả lời bằng tiếng Việt theo đúng định dạng này và KHÔNG dùng markdown:

FINAL_SUMMARY:
<một đoạn ngắn tối đa 120 từ>

FINAL_DIAGNOSIS:
- <mỗi dòng là một kết luận hoàn chỉnh>
- <không dùng heading như Issue chính, Chắc chắn, Issue phụ>
- <không dùng markdown đậm>

Yêu cầu:
- Phải bám sát user_query nếu có
- Nếu user_query chỉ tập trung vào backend/Tomcat/AJP, không được làm access control thành trọng tâm
- Dùng tool_results để cập nhật kết luận
- Phân biệt issue chính và issue phụ ngay trong nội dung câu
- Phải viết cẩn trọng, tránh khẳng định tuyệt đối nếu bằng chứng chưa đủ
- Ưu tiên các cụm: "nhiều khả năng", "cho thấy", "củng cố giả thuyết", "phù hợp với tình huống"
- Không bịa
"""

    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": "Bạn là trợ lý điều tra sự cố backend."},
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