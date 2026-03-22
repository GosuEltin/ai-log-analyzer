import asyncio
import httpx
import os
import glob
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Please install required packages: pip install mcp httpx")
    import sys; sys.exit(1)

# Khởi tạo MCP Server
mcp = FastMCP("AILogAnalyzer")

# URL API Backend của bạn (Lấy từ biến môi trường trên Server, mặc định là Localhost)
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_URL = f"{API_BASE_URL}/analyze-log"

@mcp.tool()
async def analyze_workspace_log(log_content: str, user_query: str) -> str:
    """
    Hãy dùng công cụ này phân tích log. 
    Lưu ý: Bạn (AI) phải TỰ TÌM file log trong workspace local, đọc mớ text bên trong và truyền vào biến `log_content`.
    
    Args:
        log_content: Nội dung chữ của file log bạn vừa đọc được.
        user_query: Toàn bộ câu lệnh/yêu cầu của người dùng (VD: "Đọc log và phân tích 1000 dòng đầu tiên").
    """
    try:
        # 1. Chuyển giao cho AI Log Analyzer Backend 
        files = {
            "file": ("workspace_log.txt", log_content.encode("utf-8"), "text/plain")
        }
        data = {
            "user_query": user_query
        }
        
        # Gọi sang FastAPI (Backend nội bộ trên CÙNG SERVER)
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(API_URL, files=files, data=data)
            
            if response.status_code != 200:
                return f"[Lỗi HTTP {response.status_code}]: Không thể kết nối tới Backend AI Log Analyzer tại {API_URL}."
                
            result_json = response.json()
            
            if not result_json.get("success"):
                return f"[Lỗi Backend]: {result_json}"
            
            # 2. Gom báo cáo trả về cho VS Code / Cursor
            res_data = result_json.get("result", {})
            final_summary = res_data.get("final_summary", "Không có tóm tắt")
            final_diagnosis = res_data.get("final_diagnosis", "Không có chẩn đoán")
            
            recommendations = res_data.get("recommendations", [])
            recs_text = "\n".join([f"- {r.get('text', '')}" for r in recommendations])
            
            report = (
                f"✅ **Đã phân tích thành công Log của bạn thông qua Server MCP**\n\n"
                f"🚨 **CHẨN ĐOÁN TỪ AI LOG ANALYZER** 🚨\n\n"
                f"**1. Tóm tắt:**\n{final_summary}\n\n"
                f"**2. Nguyên nhân gốc rễ (Root Cause):**\n{final_diagnosis}\n\n"
                f"**3. Khuyến nghị:**\n{recs_text}\n"
            )
            return report

    except Exception as e:
        return f"Xảy ra lỗi nghiêm trọng: {str(e)}"

if __name__ == "__main__":
    # Chạy bằng giao thức stdio để Cursor/VS Code Local tự gọi ngầm (không cần tự bật file này)
    mcp.run(transport='stdio')

