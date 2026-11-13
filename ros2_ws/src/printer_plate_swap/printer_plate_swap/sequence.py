"""플레이트 교체 동작 시퀀스 생성과 랙 슬롯 관리 (ROS 의존 없음).

전체 흐름
  0. 홈 → 프린터 앞
  1. 사용한 플레이트 빼내기: 베드 위 접근 → 하강·파지 → 살짝 들어 자석에서 분리 → 앞으로 빼냄
  2. 완료 랙에 놓기
  3. 새 플레이트 집기
  4. 프린터에 장착: 앞에서 밀어 넣기 → 베드에 내려놓기 → 놓고 후퇴
  5. 프린터 앞 → 홈
"""

import threading
from dataclasses import dataclass

from .config import offset_z


@dataclass(frozen=True)
class Step:
    kind: str          # movej | movel | open | grip | wait
    phase: str         # 웹 UI에 보여줄 공정 단계
    label: str         # 사람이 읽는 설명
    target: tuple = ()
    speed: str = "travel"  # movel 전용: travel | fine
    seconds: float = 0.0


def _movej(phase, label, joints):
    return Step("movej", phase, label, tuple(joints))


def _movel(phase, label, pose, speed="travel"):
    return Step("movel", phase, label, tuple(pose), speed)


def build_swap_sequence(cfg, done_slot, fresh_slot):
    poses, racks, motion = cfg["poses"], cfg["racks"], cfg["motion"]
    dz, peel, settle = motion["approach_dz"], motion["peel_dz"], motion["settle_sec"]

    home = poses["home_j"]
    front = poses["printer_front"]
    grip = poses["plate_grip"]
    grip_above = offset_z(grip, dz)
    grip_peel = offset_z(grip, peel)
    out = poses["plate_out"]
    done = racks["done"][done_slot]
    fresh = racks["fresh"][fresh_slot]

    P0, P1, P2, P3, P4, P5 = (
        "준비",
        "사용한 플레이트 빼내기",
        f"완료 랙 {done_slot + 1}번에 놓기",
        f"새 플레이트 집기 (랙 {fresh_slot + 1}번)",
        "새 플레이트 장착",
        "복귀",
    )
    return [
        _movej(P0, "홈 위치", home),
        Step("open", P0, "그리퍼 열기"),
        _movel(P0, "프린터 앞 안전 위치", front),

        _movel(P1, "플레이트 손잡이 위로 접근", grip_above),
        _movel(P1, "손잡이 위치로 하강", grip, "fine"),
        Step("wait", P1, "정지 안정화", seconds=settle),
        Step("grip", P1, "플레이트 파지"),
        _movel(P1, "살짝 들어 자석 베드에서 분리", grip_peel, "fine"),
        _movel(P1, "플레이트를 프린터 밖으로 빼냄", out, "fine"),
        _movel(P1, "프린터 앞 안전 위치", front),

        _movel(P2, "완료 랙 슬롯 위로 이동", offset_z(done, dz)),
        _movel(P2, "슬롯으로 하강", done, "fine"),
        Step("open", P2, "플레이트 놓기"),
        _movel(P2, "슬롯 위로 상승", offset_z(done, dz), "fine"),

        _movel(P3, "새 플레이트 슬롯 위로 이동", offset_z(fresh, dz)),
        _movel(P3, "슬롯으로 하강", fresh, "fine"),
        Step("wait", P3, "정지 안정화", seconds=settle),
        Step("grip", P3, "새 플레이트 파지"),
        _movel(P3, "슬롯 위로 상승", offset_z(fresh, dz), "fine"),

        _movel(P4, "프린터 앞 안전 위치", front),
        _movel(P4, "프린터 입구로 이동", out, "fine"),
        _movel(P4, "베드 위로 밀어 넣기", grip_peel, "fine"),
        _movel(P4, "베드에 내려놓기 (정렬 핀 맞춤)", grip, "fine"),
        Step("open", P4, "플레이트 놓기"),
        _movel(P4, "베드 위로 상승", grip_above, "fine"),
        _movel(P4, "프린터 앞 안전 위치", front),

        _movej(P5, "홈 위치", home),
    ]


class RackTracker:
    """다음에 쓸 완료/새 플레이트 슬롯 번호를 관리한다 (스레드 안전).

    교체가 끝까지 성공했을 때만 다음 슬롯으로 넘어간다. 중간에 실패하면
    작업자가 플레이트를 정리한 뒤 reset() 으로 초기화한다.
    """

    def __init__(self, n_done, n_fresh):
        self._lock = threading.Lock()
        self.n_done, self.n_fresh = n_done, n_fresh
        self.done_idx = self.fresh_idx = 0

    def next_slots(self):
        """(done_slot, fresh_slot) 또는 남은 슬롯이 없으면 사유 문자열과 None."""
        with self._lock:
            if self.done_idx >= self.n_done:
                return None, "완료 랙이 가득 찼습니다. 플레이트를 비우고 reset_racks 를 호출하세요"
            if self.fresh_idx >= self.n_fresh:
                return None, "새 플레이트 랙이 비었습니다. 채운 뒤 reset_racks 를 호출하세요"
            return (self.done_idx, self.fresh_idx), ""

    def commit(self):
        with self._lock:
            self.done_idx += 1
            self.fresh_idx += 1

    def reset(self):
        with self._lock:
            self.done_idx = self.fresh_idx = 0

    def snapshot(self):
        with self._lock:
            return {
                "done_used": self.done_idx, "done_total": self.n_done,
                "fresh_used": self.fresh_idx, "fresh_total": self.n_fresh,
            }
