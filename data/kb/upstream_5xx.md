# Runbook: Upstream 5xx Errors

## Triệu chứng
- Log xuất hiện HTTP 500, 502, 503 hoặc 504 khi gọi sang service khác.
- "Upstream service/server failure" được hệ thống phân loại.

## Bước kiểm tra
1. Sử dụng Dashboard giám sát để xác định service nào đang trả về lỗi 5xx.
2. Kiểm tra log của service đích (downstream).
3. Kiểm tra cấu hình Nginx/Ingress nếu có.
4. Xem xét tăng `CONNECT_TIMEOUT` nếu service phản hồi chậm nhưng vẫn xử lý được.
