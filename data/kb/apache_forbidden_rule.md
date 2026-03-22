# Runbook: Directory index forbidden by rule

Symptoms
- Directory index forbidden by rule
- Client bị chặn truy cập thư mục /var/www/html/

Possible causes
- thiếu DirectoryIndex
- rule deny/allow sai
- thư mục không có quyền phù hợp

First checks
1. Kiểm tra cấu hình DirectoryIndex
2. Kiểm tra quyền thư mục
3. Kiểm tra rule Allow/Deny
4. Kiểm tra file index trong /var/www/html/