# Runbook: Database Timeout

## Symptoms
- DB connection timeout
- Slow response
- Checkout requests fail

## Common causes
- Connection pool exhausted
- Slow queries
- DB overload
- Recent config change

## First checks
1. Check DB health
2. Check active connections
3. Check slow query log
4. Check latest deployment

## Severity guide
- Critical nếu checkout fail hàng loạt
- Medium nếu chỉ ảnh hưởng một phần request