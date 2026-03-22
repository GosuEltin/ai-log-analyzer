# 📡 API Documentation

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### GET `/`

Root endpoint — trả về `index.html` nếu tồn tại, hoặc health message.

**Response:**
```json
{
  "message": "AI Log Analyzer Backend is running, but index.html was not found in root."
}
```

---

### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

---

### POST `/analyze-log`

Phân tích log file bằng AI Agent pipeline 8 pha.

#### Request

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `file` | File (multipart) | ✅ | File log cần phân tích (.log, .txt) |
| `user_query` | string (form) | ❌ | Câu hỏi/hướng điều tra từ người dùng (hỗ trợ tiếng Việt lẫn tiếng Anh) |

> **Ghi chú:** `user_query` có thể chứa tiếng Việt — hệ thống tự động dịch sang tiếng Anh qua LLM trước khi phân tích. Cũng hỗ trợ cú pháp giới hạn dòng: "100 dòng đầu", "first 200 lines", "top 50 lines".

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/analyze-log \
  -F "file=@apache_error.log" \
  -F "user_query=kiểm tra kết nối backend tomcat"
```

#### Response — `AnalyzeResponse`

```json
{
  "success": true,
  "filename": "apache_error.log",
  "result": {
    "overview": { ... },
    "clusters": [ ... ],
    "probable_causes": [ ... ],
    "recommendations": [ ... ],
    "evidence": [ ... ],
    "summary": "...",
    "retrieved_knowledge": [ ... ],
    "severity": "HIGH",
    "action_checks": [ ... ],
    "executed_actions": [ ... ],
    "final_summary": "...",
    "final_diagnosis": [ ... ]
  }
}
```

---

## Response Schema Details

### `Overview`

| Field | Type | Description |
|-------|------|-------------|
| `total_lines` | int | Tổng số dòng log (parsed + failed) |
| `parsed_lines` | int | Số dòng parse thành công |
| `failed_lines` | int | Số dòng không parse được |
| `failed_lines_content` | string[] | Tối đa 50 dòng failed đầu tiên (nội dung thực) |
| `info_count` | int | Số dòng INFO |
| `warn_count` | int | Số dòng WARN |
| `error_count` | int | Số dòng ERROR |
| `top_services` | dict | Top 5 service xuất hiện nhiều nhất (service → count) |

### `ErrorCluster`

| Field | Type | Description |
|-------|------|-------------|
| `label` | string | Tên nhóm lỗi (ví dụ: "mod_jk workerEnv error state") |
| `count` | int | Số lần xuất hiện |
| `services` | string[] | Top 3 services liên quan |
| `samples` | string[] | Tối đa 3 dòng log mẫu (raw) |

### `ActionCheck`

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Tên hành động kiểm tra |
| `tool` | string | Tool sẽ dùng (`check_http_endpoint`, `check_tcp_port`, `read_file`, `read_file_tail`, `run_shell_command`) |
| `args` | dict | Arguments cho tool |
| `command` | string | Equivalent shell command tương đương |
| `purpose` | string | Mục đích kiểm tra |
| `priority` | int | Độ ưu tiên (1 = cao nhất) |
| `category` | string | Phân loại (`backend_health`, `network_connectivity`, `log_inspection`, `config_review`, `port_inspection`, `filesystem_check`, `process_inspection`) |
| `platform` | string | Platform yêu cầu (`any`, `linux`, `windows`). Default: `linux` |

### `ToolExecutionResult`

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Tên hành động |
| `tool` | string | Tool đã dùng |
| `args` | dict | Arguments đã truyền |
| `success` | bool | Kết quả thành công/thất bại |
| `output` | string | Output từ tool (content, detail, hoặc stdout) |
| `error` | string? | Thông báo lỗi (nếu có, ví dụ: platform mismatch) |
| `priority` | int | Độ ưu tiên |
| `category` | string | Phân loại |

### `severity` values

| Value | Điều kiện |
|-------|-----------|
| `"HIGH"` | `mod_jk workerEnv error state` count >= 100 |
| `"MEDIUM"` | `Directory access forbidden` count >= 20 |
| `"LOW"` | Tất cả trường hợp còn lại |

---

## Error Responses

| Status | Condition | Body |
|:------:|-----------|------|
| 400 | File không có tên | `{"detail": "Thiếu tên file."}` |
| 400 | File rỗng (0 bytes) | `{"detail": "File rỗng."}` |
| 500 | Server error | Standard FastAPI error response |
