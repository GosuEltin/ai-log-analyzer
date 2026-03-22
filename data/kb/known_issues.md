# Known Issues & Workarounds

| Vấn đề | Workaround / Fix |
|---|---|
| Lỗi parse log khi line quá dài | Tăng buffer size trong parser logic |
| `payment-service` thỉnh thoảng 504 | Tăng timeout kết nối tới Gateway lên 10s |
| Database connection pool bị full | Kiểm tra các query chưa đóng connection |
