"""M0609 모션 좌표 정의와 안전 검증 로직.

ROS / 두산 패키지에 의존하지 않는 순수 파이썬 모듈이라 로봇 없이도 테스트할 수 있다.

좌표계: 로봇 베이스 좌표계(DR_BASE), 단위 mm / deg
  - X: 로봇 정면 방향, Y: 로봇 왼쪽 방향, Z: 위쪽
  - 자세 (Rx, Ry, Rz) = (0, 180, 0)  → 툴(그리퍼)이 바닥을 향함 (ZYZ 오일러)
"""

import math

# ---------------------------------------------------------------------------
# 1. 홈 위치 (관절 좌표, deg)
#    J3=90, J5=90 → 팔이 접힌 채 툴이 아래를 향하는 두산 표준 홈 자세
# ---------------------------------------------------------------------------
HOME_J = [0.0, 0.0, 90.0, 0.0, 90.0, 0.0]

# ---------------------------------------------------------------------------
# 2. 목표 위치 4곳 (작업 좌표 [x, y, z, rx, ry, rz])
#    로봇 정면 작업대 위 300 x 300 mm 사각형의 네 꼭짓점 (위에서 본 배치)
#
#            +Y
#     P2 (450, 150)   P3 (600, 150)
#     P1 (450,-150)   P4 (600,-150)
#            -Y          → +X (로봇 정면)
# ---------------------------------------------------------------------------
TOOL_DOWN = [0.0, 180.0, 0.0]
TARGET_Z = 200.0  # 목표 높이 (작업대 높이에 맞게 조정)

TARGETS = {
    "P1": [450.0, -150.0, TARGET_Z] + TOOL_DOWN,
    "P2": [450.0, 150.0, TARGET_Z] + TOOL_DOWN,
    "P3": [600.0, 150.0, TARGET_Z] + TOOL_DOWN,
    "P4": [600.0, -150.0, TARGET_Z] + TOOL_DOWN,
}

# 목표 바로 위 접근 높이: 수평 이동은 이 높이에서만 하고, 내려갈 때는 수직으로만 이동
APPROACH_OFFSET_Z = 100.0

# ---------------------------------------------------------------------------
# 3. 속도 / 가속도 / 정밀도
# ---------------------------------------------------------------------------
JOINT_VEL = 30.0          # deg/s   (movej)
JOINT_ACC = 30.0          # deg/s^2
TRAVEL_VEL = [100.0, 30.0]  # [mm/s, deg/s] 접근 높이에서 이동 (movel)
TRAVEL_ACC = [200.0, 60.0]
FINE_VEL = [30.0, 20.0]     # 목표 지점으로 내려갈 때 저속
FINE_ACC = [60.0, 40.0]

POSITION_TOLERANCE_MM = 1.0  # 도착 후 실제 위치와 목표의 허용 오차

# ---------------------------------------------------------------------------
# 4. 안전 작업 영역 (이 범위를 벗어난 좌표는 실행 전에 거부)
# ---------------------------------------------------------------------------
WORKSPACE = {
    "x": (250.0, 750.0),
    "y": (-400.0, 400.0),
    "z": (100.0, 600.0),
}
BASE_HEIGHT_MM = 135.0  # M0609 베이스 바닥 ~ J2 축 높이
MAX_REACH_MM = 850.0    # 공칭 도달 거리 900mm에서 여유 50mm 확보


def approach_of(pos):
    """목표 좌표 바로 위(+Z) 접근 좌표를 반환한다."""
    p = list(pos)
    p[2] += APPROACH_OFFSET_Z
    return p


def validate_pose(name, pos):
    """좌표가 안전 작업 영역과 도달 거리 안에 있는지 확인한다. 문제가 있으면 ValueError."""
    if len(pos) != 6:
        raise ValueError(f"{name}: 좌표는 [x, y, z, rx, ry, rz] 6개 값이어야 합니다 ({len(pos)}개)")
    for axis, value in zip("xyz", pos[:3]):
        low, high = WORKSPACE[axis]
        if not low <= value <= high:
            raise ValueError(f"{name}: {axis}={value} 가 안전 범위 [{low}, {high}] 를 벗어났습니다")
    x, y, z = pos[:3]
    reach = math.sqrt(x * x + y * y + (z - BASE_HEIGHT_MM) ** 2)
    if reach > MAX_REACH_MM:
        raise ValueError(f"{name}: 도달 거리 {reach:.1f}mm 가 한계 {MAX_REACH_MM}mm 를 넘습니다")


def validate_all(targets=None):
    """모든 목표 좌표와 그 접근 좌표를 검증한다. 모션 시작 전에 호출한다."""
    targets = TARGETS if targets is None else targets
    if not targets:
        raise ValueError("목표 위치가 비어 있습니다")
    for name, pos in targets.items():
        validate_pose(name, pos)
        validate_pose(f"{name}(접근)", approach_of(pos))


def position_error(target, actual):
    """목표와 실제 위치의 XYZ 직선 거리 오차(mm)."""
    return math.dist(target[:3], actual[:3])
