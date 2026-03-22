Runbook: Upstream Service Failure

Triệu chứng:
- HTTP 500/502/503
- Retry nhiều lần nhưng vẫn fail
- Một service gọi service khác không thành công

Bước kiểm tra:
1. Kiểm tra health của upstream service
2. Kiểm tra timeout và retry policy
3. Kiểm tra log ở service phụ thuộc
4. Kiểm tra thay đổi deploy gần nhất