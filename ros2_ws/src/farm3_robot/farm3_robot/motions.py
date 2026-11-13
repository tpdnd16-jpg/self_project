"""공통 동작 블록: 홈 이동, 집기, 놓기 (ROS 의존 없음).

적재대·프린터·수령대 모두 같은 위치 정의(approach / target / lift_dz)를 쓰므로
집기·놓기 두 가지 동작만 조합하면 투입과 회수를 만들 수 있다.

    집기: approach → target(저속) → 잡기 → lift_dz 만큼 수직 상승 → 든 채로 approach 로 빼기
    놓기: approach+lift → target+lift(저속) → target 으로 내리기 → 놓기 → approach 로 후퇴
"""

from dataclasses import dataclass

from .positions import lifted


@dataclass(frozen=True)
class Step:
    kind: str           # movej | movel | open | grip | wait | payload
    phase: str          # 사람이 읽는 단계 설명 (feedback.phase)
    target: tuple = ()
    speed: str = "travel"   # movel 전용: travel | fine
    value: float = 0.0      # wait: 초, payload: kg


def go_home(home_j, phase):
    return [Step("movej", phase, tuple(home_j))]


def pick(loc, name, payload_kg, settle_sec):
    approach, target, dz = loc["approach"], loc["target"], loc["lift_dz"]
    return [
        Step("open", f"{name}: 그리퍼 열기"),
        Step("movel", f"{name}: 앞 접근 위치로 이동", tuple(approach)),
        Step("movel", f"{name}: 보드 위치로 진입", tuple(target), "fine"),
        Step("wait", f"{name}: 정지 안정화", value=settle_sec),
        Step("grip", f"{name}: 보드 잡기"),
        Step("payload", f"{name}: 페이로드 설정 {payload_kg}kg", value=payload_kg),
        Step("movel", f"{name}: 보드 들어 올리기", tuple(lifted(target, dz)), "fine"),
        Step("movel", f"{name}: 보드를 들고 빠져나오기", tuple(lifted(approach, dz)), "fine"),
    ]


def place(loc, name, settle_sec):
    approach, target, dz = loc["approach"], loc["target"], loc["lift_dz"]
    return [
        Step("movel", f"{name}: 앞 접근 위치로 이동", tuple(lifted(approach, dz))),
        Step("movel", f"{name}: 보드를 들고 진입", tuple(lifted(target, dz)), "fine"),
        Step("movel", f"{name}: 보드 내려놓기", tuple(target), "fine"),
        Step("wait", f"{name}: 정지 안정화", value=settle_sec),
        Step("open", f"{name}: 보드 놓기"),
        Step("payload", f"{name}: 페이로드 해제", value=0.0),
        Step("movel", f"{name}: 앞 접근 위치로 후퇴", tuple(approach), "fine"),
    ]
