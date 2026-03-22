# 📡 API Documentation

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### GET `/`

Health check root.

**Response:**
```json
{
  "message": "AI Log Analyzer is running"
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

Phân tích log file bằng AI Agent pipeline 6 pha.

#### Request

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `file` | File (multipart) | ✅ | File log cần phân tích (.log, .txt) |
| `user_query` | string (form) | ❌ | Câu hỏi/hướng điều tra từ người dùng |

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/analyze-log \
  -F "file=@apache_error.log" \
  -F "user_query=check backend tomcat AJP"
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
| `info_count` | int | Số dòng INFO |
| `warn_count` | int | Số dòng WARN |
| `error_count` | int | Số dòng ERROR |
| `top_services` | dict | Top 5 service xuất hiện nhiều nhất |

### `ErrorCluster`

| Field | Type | Description |
|-------|------|-------------|
| `label` | string | Tên nhóm lỗi (ví dụ: "mod_jk workerEnv error state") |
| `count` | int | Số lần xuất hiện |
| `services` | string[] | Top 3 services liên quan |
| `samples` | string[] | Tối đa 3 dòng log mẫu |

### `ActionCheck`

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Tên hành động kiểm tra |
| `tool` | string | Tool sẽ dùng (check_http_endpoint, check_tcp_port, ...) |
| `args` | dict | Arguments cho tool |
| `command` | string | Equivalent shell command |
| `purpose` | string | Mục đích kiểm tra |
| `priority` | int | Độ ưu tiên (1 = cao nhất) |
| `category` | string | Phân loại (backend_health, network_connectivity, ...) |
| `platform` | string | Platform yêu cầu (any, linux, windows) |

### `ToolExecutionResult`

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Tên hành động |
| `tool` | string | Tool đã dùng |
| `args` | dict | Arguments đã truyền |
| `success` | bool | Kết quả thành công/thất bại |
| `output` | string | Output từ tool |
| `error` | string? | Thông báo lỗi (nếu có) |
| `priority` | int | Độ ưu tiên |
| `category` | string | Phân loại |

---

## Error Responses

| Status | Condition | Body |
|:------:|-----------|------|
| 400 | File không có tên | `{"detail": "Thiếu tên file."}` |
| 400 | File rỗng | `{"detail": "File rỗng."}` |
| 500 | Server error | `{"detail": "Internal Server Error"}` |
