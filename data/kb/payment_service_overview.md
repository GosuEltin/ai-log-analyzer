# Overview: Payment Service

## Mô tả
`payment-service` chịu trách nhiệm xử lý các giao dịch thanh toán qua Gateway (VNPay, Momo, Stripe).

## Thành phần chính
- **API Layer**: Tiếp nhận request từ `checkout-service`.
- **Worker**: Xử lý callback/webhook từ Gateway.
- **Database**: Lưu trữ lịch sử giao dịch và trạng thái thanh toán.

## Các lỗi thường gặp
- Gateway timeout.
- Sai lệch chữ ký số (Checksum invalid).
- Database deadlock khi có quá nhiều giao dịch đồng thời.
