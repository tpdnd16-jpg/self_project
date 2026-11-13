"""보드 투입(insert) / 회수(eject) 작업.

farm3_interfaces 의 Insert.action / Eject.action 과 입력·출력 필드명을 맞췄다.
통신(Action 서버) 담당은 TaskRunner 를 그대로 감싸면 된다.

    runner = TaskRunner(cfg, robot, gripper)
    result = runner.insert(work_id, start_pos_id, printer_pos_id, feedback_cb)
    # result   = {"success", "message", "work_id", "work_type"}            → Insert.Result
    # feedback = {"start_at", "end_at", "work_id", "step", "total", "phase"} → Insert.Feedback
    # start_at / end_at 은 epoch 초(float). end_at 은 진행 중 0.0, 마지막 feedback 에서 채워짐.

순서
    INSERT : 홈 → 적재대[start_pos_id] 집기 → 홈 → 프린터[printer_pos_id] 놓기 → 홈
    EJECT  : 홈 → 프린터[printer_pos_id] 집기 → 홈 → 수령대[receive_pos_id] 놓기 → 홈
"""

import threading
import time

from .motions import go_home, pick, place
from .positions import LocationError, get_location

WORK_TYPE_INSERT = 0  # Insert.Result.WORK_TYPE_INSERT 와 같은 값
WORK_TYPE_EJECT = 1


class GripError(RuntimeError):
    pass


class StopRequested(RuntimeError):
    pass


# ---------------------------------------------------------------------------
def _weight(cfg, key, dry_run):
    kg = cfg["payload"][key]
    if kg is None:
        if dry_run:
            return 0.0
        raise LocationError(f"보드 무게(payload.{key})가 아직 입력되지 않았습니다")
    return float(kg)


def _transfer(cfg, src_kind, src_id, src_name, dst_kind, dst_id, dst_name, weight_key, via_home, dry_run=False):
    src = get_location(cfg, src_kind, src_id)
    dst = get_location(cfg, dst_kind, dst_id)
    kg = _weight(cfg, weight_key, dry_run)
    settle = cfg["motion"]["settle_sec"]
    home = cfg["home_j"]

    steps = go_home(home, "홈 위치에서 시작")
    steps += pick(src, src_name, kg, settle)
    if via_home:
        steps += go_home(home, "보드를 들고 홈 경유")
    steps += place(dst, dst_name, settle)
    steps += go_home(home, "홈 위치로 복귀")
    return steps


def build_insert(cfg, start_pos_id, printer_pos_id, dry_run=False):
    return _transfer(
        cfg, "stackers", start_pos_id, f"적재대 {start_pos_id}번",
        "printers", printer_pos_id, f"프린터 {printer_pos_id}번",
        "board_empty_kg", cfg["motion"]["via_home"]["insert"], dry_run,
    )


def build_eject(cfg, printer_pos_id, receive_pos_id, dry_run=False):
    return _transfer(
        cfg, "printers", printer_pos_id, f"프린터 {printer_pos_id}번",
        "receivers", receive_pos_id, f"수령대 {receive_pos_id}번",
        "board_printed_kg", cfg["motion"]["via_home"]["eject"], dry_run,
    )


# ---------------------------------------------------------------------------
class TaskRunner:
    """작업 1개씩 실행. robot / gripper 는 robot_io 의 객체(또는 테스트용 가짜)."""

    def __init__(self, cfg, robot, gripper, clock=time.time, dry_run=False, log=None):
        self.cfg, self.robot, self.gripper = cfg, robot, gripper
        self.clock, self.dry_run = clock, dry_run
        self.log = log or (lambda msg: None)
        self._busy = threading.Lock()
        self._stop = threading.Event()

    # --- 통신 담당이 호출하는 함수 ------------------------------------------
    def insert(self, work_id, start_pos_id, printer_pos_id, feedback_cb=None):
        return self._run(
            work_id, WORK_TYPE_INSERT,
            lambda: build_insert(self.cfg, start_pos_id, printer_pos_id, self.dry_run), feedback_cb,
        )

    def eject(self, work_id, printer_pos_id, receive_pos_id, feedback_cb=None):
        return self._run(
            work_id, WORK_TYPE_EJECT,
            lambda: build_eject(self.cfg, printer_pos_id, receive_pos_id, self.dry_run), feedback_cb,
        )

    def request_stop(self):
        """진행 중인 작업을 현재 동작이 끝난 뒤 멈춘다 (action cancel 용).
        동작 도중 즉시 정지는 비상정지 버튼으로 한다."""
        self._stop.set()

    @property
    def busy(self):
        return self._busy.locked()

    # --- 내부 ----------------------------------------------------------------
    def _run(self, work_id, work_type, build, feedback_cb):
        def result(success, message):
            return {"success": success, "message": message, "work_id": work_id, "work_type": work_type}

        if not self._busy.acquire(blocking=False):
            return result(False, "로봇이 다른 작업 중입니다")
        try:
            self._stop.clear()
            try:
                steps = build()  # 좌표·무게 확인. 실패하면 로봇은 움직이지 않는다
            except LocationError as e:
                return result(False, f"작업 거부: {e}")

            start_at = self.clock()
            total = len(steps)
            feedback_cb = feedback_cb or (lambda fb: None)
            try:
                for i, step in enumerate(steps, 1):
                    if self._stop.is_set():
                        raise StopRequested(f"{i}/{total} 단계 전에 중지 요청됨")
                    self.log(f"[work {work_id}] {i:2d}/{total} {step.phase}")
                    feedback_cb({"start_at": start_at, "end_at": 0.0, "work_id": work_id,
                                 "step": i, "total": total, "phase": step.phase})
                    self._do(step)
            except StopRequested as e:
                return result(False, f"작업 중지: {e}. 로봇 위치를 확인하세요")
            except GripError as e:
                return result(False, f"{e}. 로봇이 정지했습니다. 보드 상태를 확인하세요")
            except Exception as e:  # 로봇 알람, 통신 오류 등
                return result(False, f"모션 오류: {e}")

            end_at = self.clock()
            feedback_cb({"start_at": start_at, "end_at": end_at, "work_id": work_id,
                         "step": total, "total": total, "phase": "완료"})
            kind = "투입" if work_type == WORK_TYPE_INSERT else "회수"
            return result(True, f"보드 {kind} 완료 ({end_at - start_at:.1f}초)")
        finally:
            self._busy.release()

    def _do(self, step):
        m = self.cfg["motion"]
        s = m["velocity_scale"]
        if step.kind == "movej":
            self.robot.movej(list(step.target), vel=m["joint_vel"] * s, acc=m["joint_acc"] * s)
        elif step.kind == "movel":
            self.robot.movel(
                list(step.target),
                vel=[v * s for v in m[f"{step.speed}_vel"]],
                acc=[a * s for a in m[f"{step.speed}_acc"]],
            )
        elif step.kind == "open":
            self.gripper.open()
        elif step.kind == "grip":
            if not self.gripper.grip():
                raise GripError(f"'{step.phase}' 실패: 그리퍼에 보드가 감지되지 않았습니다")
        elif step.kind == "wait":
            self.robot.wait(step.value)
        elif step.kind == "payload":
            self.robot.set_payload(step.value, self.cfg["payload"]["cog"])
        else:
            raise ValueError(f"알 수 없는 단계: {step.kind}")
