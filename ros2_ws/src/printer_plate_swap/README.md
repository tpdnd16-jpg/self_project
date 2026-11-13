# printer_plate_swap — 3D 프린터 빌드 플레이트 자동 교체

Doosan M0609 + OnRobot RG2가 출력이 끝난 3D 프린터의 빌드 플레이트를 빼서 완료 랙에 놓고,
새 플레이트를 집어 프린터에 다시 장착하는 ROS 2 패키지입니다.

## 동작 순서

```
홈 ─► 프린터 앞 ─► [사용한 플레이트 빼내기] ─► [완료 랙에 놓기] ─► [새 플레이트 집기] ─► [프린터에 장착] ─► 프린터 앞 ─► 홈

사용한 플레이트 빼내기: 손잡이 위 접근 → 저속 하강 → 파지 → 15mm 들어 자석 분리 → 앞으로 빼냄
새 플레이트 장착     : 프린터 입구 → 베드 위로 밀어 넣기 → 베드에 내려놓기(정렬 핀) → 놓기 → 상승
```

- 프린터 내부와 랙 근처에서는 모두 **저속(fine)** 으로, 공중 이동은 **travel 속도**로 움직입니다.
- 프린터 출입은 항상 `printer_front`(문 바깥 안전 위치)를 거칩니다.
- 파지에 실패하면(플레이트 미감지) **그 자리에서 정지**합니다. 프린터 안에서 자동으로 움직이면 충돌할 수 있어서 자동 복귀는 하지 않습니다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `config/plate_swap.yaml` | **좌표·속도·그리퍼 설정. 현장에서는 이 파일만 고치면 됩니다** |
| `printer_plate_swap/sequence.py` | 교체 동작 순서 정의, 랙 슬롯 관리 |
| `printer_plate_swap/executor.py` | 순서대로 로봇·그리퍼 실행, 중지·파지 실패 처리 |
| `printer_plate_swap/gripper.py` | RG2 제어 (mock / OnRobot Modbus TCP / 컨트롤러 디지털 출력) |
| `printer_plate_swap/config.py` | 설정 검증 (작업 영역·도달 거리 밖 좌표가 있으면 시작 거부) |
| `printer_plate_swap/swap_node.py` | ROS 2 노드 (서비스·상태 토픽) |
| `printer_plate_swap/print_pose.py` | 좌표 교시 도우미 |

## ROS 2 인터페이스 (웹 담당과 공유)

| 종류 | 이름 | 타입 | 설명 |
|---|---|---|---|
| 서비스 | `/plate_swap/start` | `std_srvs/srv/Trigger` | 교체 1회 시작 (다음 빈 슬롯 자동 선택) |
| 서비스 | `/plate_swap/abort` | `std_srvs/srv/Trigger` | 현재 동작이 끝나면 중지 |
| 서비스 | `/plate_swap/reset_racks` | `std_srvs/srv/Trigger` | 랙을 비우거나 채운 뒤 슬롯 카운터 초기화 |
| 토픽 | `/plate_swap/status` | `std_msgs/msg/String` (JSON) | 1초마다, 그리고 단계가 바뀔 때마다 발행 |

상태 JSON 예시:
```json
{"state": "RUNNING", "phase": "사용한 플레이트 빼내기", "step": 7, "total": 27,
 "message": "플레이트 파지", "racks": {"done_used": 0, "done_total": 2, "fresh_used": 0, "fresh_total": 2}}
```
`state`: `IDLE` / `RUNNING` / `DONE` / `ERROR` / `ABORTED`

웹(roslibjs)에서 호출하는 예:
```js
const start = new ROSLIB.Service({ ros, name: '/plate_swap/start', serviceType: 'std_srvs/srv/Trigger' });
start.callService({}, res => console.log(res.success, res.message));
new ROSLIB.Topic({ ros, name: '/plate_swap/status', messageType: 'std_msgs/msg/String' })
  .subscribe(msg => console.log(JSON.parse(msg.data)));
```

## 빌드
```bash
cd ros2_ws
colcon build --packages-select printer_plate_swap
source install/setup.bash
```

## 진행 순서 (시운전)

### 1단계: 로봇 없이 순서 확인 (dry run)
```bash
ros2 launch printer_plate_swap plate_swap.launch.py dry_run:=true
```
```bash
ros2 service call /plate_swap/start std_srvs/srv/Trigger
```

### 2단계: 좌표 교시
드라이버를 실제 로봇 모드로 띄웁니다.
```bash
ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py mode:=real host:=<컨트롤러 IP> model:=m0609
```
```bash
ros2 run printer_plate_swap print_pose
```
티치 펜던트 직접 교시로 로봇을 각 위치에 옮기고 Enter를 누르면 좌표가 출력됩니다.
출력된 좌표를 `config/plate_swap.yaml`의 `poses`, `racks`에 붙여 넣으세요.

| 이름 | 교시 위치 |
|---|---|
| `printer_front` | 프린터 문 바깥, 아무것도 부딪히지 않는 높이 |
| `plate_grip` | 베드 위 플레이트 손잡이를 **잡을 수 있는 정확한 위치** (손가락이 탭을 감싸는 높이) |
| `plate_out` | 플레이트를 15mm 들어 앞으로 빼서 프린터 프레임을 벗어난 위치 |
| `racks.done[n]` | 완료 플레이트를 놓을 슬롯 (놓는 높이) |
| `racks.fresh[n]` | 새 플레이트를 집을 슬롯 (잡는 높이) |

### 3단계: 가상 모드로 경로 확인
```bash
ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py mode:=virtual model:=m0609 host:=127.0.0.1
```
```bash
ros2 launch printer_plate_swap plate_swap.launch.py
```
RViz에서 경로를 확인합니다.

### 4단계: 실제 로봇
- `velocity_scale: 0.2`로 시작하고, 티치 펜던트 속도도 낮춘 상태에서 비상정지 버튼을 손에 쥐고 실행하세요.
- 그리퍼 연결 방식에 맞게 `gripper.backend`를 바꾸세요.
  - `onrobot_modbus`: Compute Box IP 입력. `pip install pymodbus`가 필요하고, 파지 감지가 됩니다.
  - `dsr_io`: 컨트롤러 디지털 출력 번호를 입력합니다. 파지 감지가 안 되므로 시운전 때 눈으로 확인해야 합니다.

## 테스트 (ROS 없이)
```bash
cd ros2_ws/src/printer_plate_swap
python3 -m unittest discover -s test -v
```

## 팀과 맞춰야 할 것 (가정한 부분)
- 플레이트는 자석식 탈착 플레이트이고, 앞쪽 손잡이(탭)를 위에서 잡는다고 가정했습니다.
- 프린터 "출력 완료" 감지와 "다음 출력 시작"은 웹/프린터 담당 쪽에서 처리하고, 이 노드는 `/plate_swap/start`로 호출된다고 가정했습니다.
- 랙은 위가 열린 슬롯에 플레이트를 세로로 꽂는 대신, 위에서 내려놓는 방식으로 가정했습니다. 다르면 `sequence.py`의 해당 단계를 수정하세요.
