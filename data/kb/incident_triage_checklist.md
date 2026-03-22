# Incident Triage Checklist

Khi phát hiện sự cố tăng vọt ERROR trong log, thực hiện các bước sau:

- [ ] **Xác định phạm vi**: Chỉ một service hay toàn bộ hệ thống bị ảnh hưởng?
- [ ] **Kiểm tra Deployment**: Có bản build mới nào vừa được đẩy lên không? (Rollback nếu cần).
- [ ] **Kiểm tra Infrastructure**: CPU, RAM, Disk của server/container có quá tải không?
- [ ] **Phân loại lỗi**: Sử dụng tool analyzer để xem nhóm lỗi chiếm đa số (DB, Auth, Upstream).
- [ ] **Liên lạc**: Thông báo cho các bên liên quan qua kênh Slack/Telegram sự cố.
