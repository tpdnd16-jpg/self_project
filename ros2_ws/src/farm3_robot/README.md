# farm3_robot — 3D 프린터 보드 투입/회수 로봇 동작

Doosan M0609 + OnRobot RG2로 3D 프린터 팜의 보드를 **투입(insert)**·**회수(eject)** 하는 로봇 동작 코드입니다.
통신(Action 서버, DB)은 포함하지 않습니다. 통신 담당이 `TaskRunner`를 감싸서 Action 서버를 만듭니다.

## 동작 순서

```
INSERT : 홈 → 적재대[start_pos_id]에서 집기 → 홈 → 프린터[printer_pos_id]에 놓기 → 홈
EJECT  : 홈 → 프린터[printer_pos_id]에서 집기 → 홈 → 수령대[receive_pos_id]에 놓기 → 홈
```

적재대, 프린터, 수령대는 모두 같은 방식으로 정의되고, **집기**와 **놓기** 두 동작의 조합으로 움직입니다.

| 항목 | 의미 |
|---|---|
| `approach` | 장비 앞 안전 위치. 여기서 수평으로 들어가고 나옵니다 |
| `target` | 보드를 잡거나 내려놓는 정확한 위치 |
| `lift_dz` | 보드를 잡은 뒤 들어 올리는 높이 (mm) |

```
집기: approach → target(저속) → 정지 → 잡기(감지 확인) → 페이로드 설정
      → lift_dz만큼 수직 상승 → 든 채로 approach로 빼기
놓기: approach+lift → target+lift(저속) → target으로 내리기 → 정지 → 놓기
      → 페이로드 해제 → approach로 후퇴
```

- 장비 안쪽은 저속(`fine`), 장비 앞까지는 일반 속도(`travel`), 홈 이동은 관절 이동(`movej`)입니다.
- 홈 경유는 `motion.via_home.insert / eject`로 켜고 끌 수 있습니다. 기본값은 둘 다 켜짐입니다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `config/positions.yaml` | **위치 ID별 좌표, 보드 무게, 속도, 그리퍼 설정. 값은 여기에만 입력** |
| `farm3_robot/positions.py` | 설정 검증, 위치 ID → 좌표 조회 |
| `farm3_robot/motions.py` | 공통 동작 블록 (홈 이동, 집기, 놓기) |
| `farm3_robot/tasks.py` | `TaskRunner.insert()` / `eject()`: 인터페이스와 같은 입력과 출력 |
| `farm3_robot/robot_io.py` | 두산 로봇 연결, RG2 그리퍼 (mock / Modbus / 디지털 출력), dry-run |
| `farm3_robot/run_task.py` | 통신 없이 단독 실행하는 도구 |
| `test/test_farm3_robot.py` | ROS 없이 돌아가는 단위 테스트 24개 |

인터페이스 정의는 옆 패키지 `farm3_interfaces/action/Insert.action`, `Eject.action`에 있습니다.

## 인터페이스 이름 대응표

원래 노션 정의는 ROS 2 이름 규칙(숫자 시작 금지, 소문자 snake_case, enum·date_time 타입 없음)에 맞지 않아서 다음과 같이 바꿨습니다.

| 노션 원래 이름 | 실제 이름 | 비고 |
|---|---|---|
| `/3farm/insert`, `/3farm/eject` | `/farm3/insert`, `/farm3/eject` | 이름이 숫자로 시작할 수 없음 |
| `insert.action` / `eject.action` | `Insert.action` / `Eject.action` | 파일명은 대문자로 시작 |
| `Work_ID int8` | `work_id int32` | int8은 127까지만 가능 |
| `Start_Pos_ID` | `start_pos_id` (int8) | 적재대 ID |
| `3D_Pos_ID` | `printer_pos_id` (int8) | 프린터 ID |
| `Receive_Pos_ID` | `receive_pos_id` (int8) | 수령대 ID |
| `Success`, `message` | `success`, `message` | |
| `Work_Type enum(insert, eject)` | `uint8 work_type` | 상수 `WORK_TYPE_INSERT=0`, `WORK_TYPE_EJECT=1` |
| `Start_At`, `End_At date_time` | `start_at`, `end_at` (`builtin_interfaces/Time`) | `end_at`은 진행 중 0, 끝나면 채워짐 |
| (추가) | `step`, `total`, `phase` | 진행 단계 표시용 feedback |

## 통신 담당용 사용법

```python
from farm3_robot.positions import load_config
from farm3_robot.robot_io import connect_dsr, make_gripper
from farm3_robot.tasks import TaskRunner

cfg = load_config(".../positions.yaml")
robot, dsr = connect_dsr(cfg["robot"]["id"], cfg["robot"]["model"])   # rclpy.init() 이후
runner = TaskRunner(cfg, robot, make_gripper(cfg["gripper"], dsr=dsr))

result = runner.insert(work_id, start_pos_id, printer_pos_id, feedback_cb)
result = runner.eject(work_id, printer_pos_id, receive_pos_id, feedback_cb)
runner.request_stop()   # action cancel: 현재 동작이 끝나면 멈춤
```

| 반환값 | 형태 | 변환 대상 |
|---|---|---|
| `result` | `{"success", "message", "work_id", "work_type"}` | `Insert.Result` / `Eject.Result` |
| `feedback_cb(fb)` | `{"start_at", "end_at", "work_id", "step", "total", "phase"}` | `Insert.Feedback` / `Eject.Feedback` |

- `start_at` / `end_at`은 epoch 초(float)입니다. `builtin_interfaces/Time`으로 바꿀 때는 `sec = int(t)`, `nanosec = int((t % 1) * 1e9)`로 나누세요.
- 이미 작업 중이면 바로 `success=False, "로봇이 다른 작업 중입니다"`를 반환합니다. 대기열 처리는 서버/DB 쪽에서 합니다.
- 좌표나 무게가 비어 있는 ID를 요청하면 **로봇을 움직이기 전에** `success=False`로 거부합니다.
- 보드를 잡지 못하면(그리퍼 미감지) 그 자리에서 정지하고 `success=False`를 반환합니다. 장비 안에서 자동으로 움직이면 충돌할 수 있어서 자동 복귀는 하지 않습니다.
- DSR 함수는 호출 중에 자기 노드를 직접 spin합니다. 그래서 Action 서버 노드와 `connect_dsr()`가 만드는 노드는 **서로 다른 노드·스레드**로 두세요.

## 좌표와 무게 입력

1. 지금 비어 있는 항목을 확인합니다.
   ```bash
   ros2 run farm3_robot run_task check
   ```
2. 티치 펜던트 직접 교시로 로봇을 각 장비의 `approach`와 `target`에 옮기고, 펜던트에 표시된 베이스 좌표 `[x, y, z, rx, ry, rz]`를 `config/positions.yaml`에 입력합니다.
3. `payload.board_empty_kg`(새 보드)와 `board_printed_kg`(출력물이 올라간 보드)를 입력합니다.
4. 적재대·프린터·수령대가 더 있으면 같은 형식으로 ID를 추가합니다. ID는 int8 범위(-128~127) 정수입니다.

작업 영역이나 팔 도달 거리를 벗어난 좌표가 있으면 실행이 시작되지 않습니다. `lift_dz`만큼 들어 올린 위치도 함께 검사합니다.

## 빌드
```bash
cd ros2_ws
colcon build --packages-select farm3_interfaces farm3_robot
source install/setup.bash
```

## 실행

로봇 없이 순서만 확인합니다. 좌표가 비어 있으면 거부되니, 좌표를 넣은 설정으로 실행하세요.
```bash
ros2 run farm3_robot run_task insert --work-id 1 --start-pos 1 --printer-pos 1 --dry-run
```
```bash
ros2 run farm3_robot run_task eject --work-id 2 --printer-pos 1 --receive-pos 1 --dry-run
```

실제 로봇에서는 먼저 두산 드라이버를 실행하고,
```bash
ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py mode:=real host:=<컨트롤러 IP> model:=m0609
```
다른 터미널에서 작업을 실행합니다.
```bash
ros2 run farm3_robot run_task insert --work-id 1 --start-pos 1 --printer-pos 1
```
경로를 먼저 확인하려면 드라이버를 `mode:=virtual host:=127.0.0.1`로 띄우세요.

## 테스트 (ROS 없이 가능)
```bash
cd ros2_ws/src/farm3_robot
python3 -m unittest discover -s test -v
```

## 실제 로봇 전 확인사항
- **TCP 등록:** RG2 그리퍼 길이만큼 TCP가 티치 펜던트에 등록돼 있어야 좌표가 그리퍼 끝 기준이 됩니다.
- **첫 실행:** `motion.velocity_scale: 0.2`로 낮추고, 비상정지 버튼을 손에 쥔 상태에서 실행하세요.
- **그리퍼 연결 방식:** `gripper.backend`를 맞춰 주세요.
  - `onrobot_modbus`: Compute Box IP를 입력하고 `pip install pymodbus`가 필요합니다. 레지스터 번호(장치 ID 65, 상태 268)는 OnRobot 매뉴얼로 꼭 확인하세요.
  - `dsr_io`: 디지털 출력 번호를 입력합니다. 파지 감지가 안 되므로 첫 시운전 때 눈으로 확인하세요.
- **페이로드:** `set_workpiece_weight`는 두산 패키지 버전에 따라 없거나 인자가 다를 수 있습니다. 함수가 없으면 경고 로그만 남기고 계속 진행합니다.
