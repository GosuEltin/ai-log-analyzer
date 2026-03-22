# Directory index forbidden by rule

## Symptoms
- Directory index forbidden by rule
- Client không truy cập được thư mục /var/www/html/

## Possible causes
- thiếu index.html
- DirectoryIndex chưa cấu hình đúng
- rule Require / Allow / Deny chặn truy cập
- .htaccess ghi đè cấu hình

## First checks
1. Kiểm tra DirectoryIndex
2. Kiểm tra index.html
3. Kiểm tra Require all granted / denied
4. Kiểm tra .htaccess và AllowOverride