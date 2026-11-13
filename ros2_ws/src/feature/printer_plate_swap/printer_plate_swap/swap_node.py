"""3D 프린터 플레이트 교체 ROS 2 노드.

인터페이스 (웹/Flask 쪽에서 rosbridge 로 호출 가능)
  서비스  /plate_swap/start        std_srvs/Trigger   교체 1회 시작 (다음 빈 슬롯 자동 선택)
  서비스  /plate_swap/abort        std_srvs/Trigger   현재 동작이 끝나면 중지
  서비스  /plate_swap/reset_racks  std_srvs/Trigger   랙 슬롯 카운터 초기화 (랙 정리 후)
  토픽    /plate_swap/status       std_msgs/String    JSON 상태 (state, phase, step, total, message, racks)

파라미터
  config_file  설정 YAML 경로 (기본: 패키지 config/plate_swap.yaml)
  dry_run      true 면 로봇 없이 동작 순서만 로그로 확인
  run_on_start true 면 시작하자마자 교체 1회 실행

구조
  DSR_ROBOT2 함수는 호출 중에 자기 노드를 직접 spin 하므로, 서비스용 노드(plate_swap)는
  별도 스레드에서 돌리고 실제 모션은 메인 스레드에서 작업 큐를 받아 실행한다.
"""

import json
import os
import queue
import threading
import time

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

from .config import ConfigError, load_config
from .executor import AbortRequested, GripError, SequenceExecutor
from .gripper import make_gripper
from .sequence import RackTracker, build_swap_sequence


def default_config_path():
    try:
        from ament_index_python.packages import get_package_share_directory

        return os.path.join(get_package_share_directory("printer_plate_swap"), "config", "plate_swap.yaml")
    except Exception:
        return os.path.join(os.path.dirname(__file__), "..", "config", "plate_swap.yaml")


class DryRunRobot:
    def __init__(self, log):
        self.log = log

    def movej(self, joints, vel, acc):
        self.log(f"  movej {joints} vel={vel:.1f}")

    def movel(self, pose, vel, acc):
        self.log(f"  movel {pose[:3]} vel={[round(v, 1) for v in vel]}")

    def wait(self, sec):
        time.sleep(min(sec, 0.05))


class DsrRobot:
    """DSR_ROBOT2 함수를 실행기 인터페이스에 맞춘 어댑터."""

    def __init__(self, dsr, common):
        self.dsr, self.c = dsr, common

    @staticmethod
    def _check(ret, what):
        if isinstance(ret, int) and ret < 0:
            raise RuntimeError(f"{what} 실패 (반환값 {ret}). 티치 펜던트 알람을 확인하세요")

    def movej(self, joints, vel, acc):
        self._check(self.dsr.movej(self.c.posj(*joints), vel=vel, acc=acc), "movej")

    def movel(self, pose, vel, acc):
        self._check(self.dsr.movel(self.c.posx(*pose), vel=vel, acc=acc, ref=self.dsr.DR_BASE), "movel")

    def wait(self, sec):
        self.dsr.wait(sec)


class PlateSwapInterface(Node):
    def __init__(self):
        super().__init__("plate_swap")
        self.declare_parameter("config_file", default_config_path())
        self.declare_parameter("dry_run", False)
        self.declare_parameter("run_on_start", False)

        self.jobs = queue.Queue()
        self.busy = threading.Event()
        self.abort = threading.Event()
        self.racks = None  # main()에서 설정 로드 후 채움
        self._last_status = {"state": "IDLE"}

        self.status_pub = self.create_publisher(String, "~/status", 10)
        self.create_service(Trigger, "~/start", self._on_start)
        self.create_service(Trigger, "~/abort", self._on_abort)
        self.create_service(Trigger, "~/reset_racks", self._on_reset)
        self.create_timer(1.0, lambda: self._publish(self._last_status))  # 웹 화면 갱신용 주기 발행

    def request_swap(self):
        """교체 작업 1회를 큐에 넣는다. (성공 여부, 메시지)"""
        if self.busy.is_set():
            return False, "이미 교체 작업이 진행 중입니다"
        slots, reason = self.racks.next_slots()
        if slots is None:
            return False, reason
        self.busy.set()
        self.abort.clear()
        self.jobs.put(slots)
        return True, f"교체 시작: 완료 랙 {slots[0] + 1}번, 새 플레이트 {slots[1] + 1}번"

    def _on_start(self, _req, res):
        res.success, res.message = self.request_swap()
        return res

    def _on_abort(self, _req, res):
        if not self.busy.is_set():
            res.success, res.message = False, "진행 중인 작업이 없습니다"
        else:
            self.abort.set()
            res.success, res.message = True, "현재 동작이 끝나면 중지합니다"
        return res

    def _on_reset(self, _req, res):
        if self.busy.is_set():
            res.success, res.message = False, "작업 중에는 초기화할 수 없습니다"
        else:
            self.racks.reset()
            res.success, res.message = True, "랙 슬롯 카운터를 초기화했습니다"
            self.set_status("IDLE", message="랙 초기화됨")
        return res

    def set_status(self, state, phase="", step=0, total=0, message=""):
        self._last_status = {
            "state": state, "phase": phase, "step": step, "total": total,
            "message": message, "racks": self.racks.snapshot() if self.racks else {},
            "stamp": time.time(),
        }
        self._publish(self._last_status)

    def _publish(self, status):
        self.status_pub.publish(String(data=json.dumps(status, ensure_ascii=False)))


def main(args=None):
    rclpy.init(args=args)
    iface = PlateSwapInterface()
    log = iface.get_logger()

    config_file = iface.get_parameter("config_file").value
    dry_run = iface.get_parameter("dry_run").value
    try:
        cfg = load_config(config_file)
    except (OSError, ConfigError) as e:
        log.error(f"설정 파일 오류 ({config_file}): {e}")
        rclpy.shutdown()
        return
    iface.racks = RackTracker(len(cfg["racks"]["done"]), len(cfg["racks"]["fresh"]))
    log.info(f"설정 로드: {config_file}")

    # --- 로봇 / 그리퍼 준비 -------------------------------------------------
    if dry_run:
        robot = DryRunRobot(log.info)
        gripper = make_gripper({"gripper": {"backend": "mock"}}, log=log.info)
        log.warn("DRY RUN 모드: 로봇을 움직이지 않고 동작 순서만 출력합니다")
    else:
        import DR_init

        robot_id, robot_model = cfg["robot"]["id"], cfg["robot"]["model"]
        DR_init.__dsr__id = robot_id
        DR_init.__dsr__model = robot_model
        dsr_node = rclpy.create_node("plate_swap_dsr", namespace=robot_id)
        DR_init.__dsr__node = dsr_node
        try:
            import DR_common2
            import DSR_ROBOT2
        except ImportError as e:
            log.error(f"두산 ROS 2 패키지를 불러오지 못했습니다: {e}")
            rclpy.shutdown()
            return
        robot = DsrRobot(DSR_ROBOT2, DR_common2)
        try:
            gripper = make_gripper(cfg, dsr=DSR_ROBOT2, log=log.info)
        except Exception as e:
            log.error(f"그리퍼 초기화 실패: {e}")
            rclpy.shutdown()
            return

    # --- 서비스 노드는 별도 스레드에서 spin ----------------------------------
    executor = SingleThreadedExecutor()
    executor.add_node(iface)
    threading.Thread(target=executor.spin, daemon=True).start()

    def on_progress(i, total, step):
        log.info(f"[{i:2d}/{total}] {step.phase} | {step.label}")
        iface.set_status("RUNNING", step.phase, i, total, step.label)

    runner = SequenceExecutor(robot, gripper, cfg["motion"], on_progress, iface.abort.is_set)

    iface.set_status("IDLE", message="대기 중")
    log.info("준비 완료. 'ros2 service call /plate_swap/start std_srvs/srv/Trigger' 로 교체를 시작하세요")
    if iface.get_parameter("run_on_start").value:
        ok, msg = iface.request_swap()
        log.info(msg) if ok else log.error(msg)

    # --- 메인 루프: 작업 큐 처리 ---------------------------------------------
    try:
        while rclpy.ok():
            try:
                done_slot, fresh_slot = iface.jobs.get(timeout=0.5)
            except queue.Empty:
                continue
            steps = build_swap_sequence(cfg, done_slot, fresh_slot)
            t0 = time.monotonic()
            try:
                runner.run(steps)
                iface.racks.commit()
                msg = f"교체 완료 ({time.monotonic() - t0:.1f}초)"
                log.info(msg)
                iface.set_status("DONE", "완료", len(steps), len(steps), msg)
            except AbortRequested as e:
                log.warn(f"작업 중지: {e}")
                iface.set_status("ABORTED", message=f"{e}. 로봇 위치를 확인한 뒤 수동으로 복귀하세요")
            except GripError as e:
                log.error(str(e))
                iface.set_status("ERROR", message=f"{e}. 로봇이 정지했습니다. 플레이트 상태를 확인하세요")
            except Exception as e:
                log.error(f"모션 오류: {e}")
                iface.set_status("ERROR", message=f"모션 오류: {e}")
            finally:
                iface.busy.clear()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
