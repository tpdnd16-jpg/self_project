# 3D 프린터 상태 (p3d_printer 가 /printer/status 로 발행)
uint8 STATE_IDLE=0
uint8 STATE_PRINTING=1
uint8 STATE_DONE=2       # 출력 완료, 플레이트 교체 필요
uint8 STATE_PAUSED=3
uint8 STATE_ERROR=4
uint8 STATE_OFFLINE=5

builtin_interfaces/Time stamp
uint8 printer_id
uint8 state
float32 progress         # 0.0 ~ 100.0 (%)
float32 bed_temp         # degC
float32 nozzle_temp      # degC
string job_name
string message
