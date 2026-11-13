# 로봇 상태 (p3d_robot_control 이 /robot/state 로 발행)
uint8 STATE_IDLE=0
uint8 STATE_MOVING=1
uint8 STATE_ERROR=2
uint8 STATE_DISCONNECTED=3

builtin_interfaces/Time stamp
uint8 state
float64[6] tcp_pose      # [x, y, z, rx, ry, rz] mm / deg, 베이스 좌표계
float64[6] joints        # [j1..j6] deg
string message
