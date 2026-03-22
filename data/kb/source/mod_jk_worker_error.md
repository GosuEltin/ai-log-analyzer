# mod_jk workerEnv error state

## Symptoms
- mod_jk child workerEnv in error state 6
- mod_jk child workerEnv in error state 7
- mod_jk child workerEnv in error state 8
- mod_jk child workerEnv in error state 9
- mod_jk child workerEnv in error state 10

## Possible causes
- backend worker không phản hồi
- workers2.properties cấu hình sai
- Apache kết nối tới backend lỗi
- worker process bị crash hoặc restart bất thường

## First checks
1. Kiểm tra workers2.properties
2. Kiểm tra backend service
3. Kiểm tra restart gần đây
4. Kiểm tra network giữa Apache và backend