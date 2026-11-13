# 공정 상태 (p3d_task_manager 가 /task/status 로 발행, 웹 화면 표시용)
builtin_interfaces/Time stamp
string task_id
string state             # IDLE / WAIT_PRINT / SWAPPING / STARTING_PRINT / ERROR / STOPPED
string phase             # 세부 단계 (사람이 읽는 문장)
uint32 step
uint32 total
string message
