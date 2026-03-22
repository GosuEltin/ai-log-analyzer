# Runbook: Authentication & Authorization Failure

## Triệu chứng
- HTTP 401 Unauthorized
- HTTP 403 Forbidden
- Lỗi "Invalid Token" hoặc "Permission Denied" trong log

## Bước kiểm tra
1. Xác nhận token JWT còn hạn hay không.
2. Kiểm tra cấu hình `SECRET_KEY` ở các service có khớp nhau không.
3. Kiểm tra phân quyền (RBAC/ABAC) của user/service đang gọi.
4. Kiểm tra log của Authentication Service.
