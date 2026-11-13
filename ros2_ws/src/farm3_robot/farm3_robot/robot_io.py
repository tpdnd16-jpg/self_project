"""로봇·그리퍼 하드웨어 연결.

TaskRunner 가 요구하는 인터페이스
  robot  : movej(joints, vel, acc), movel(pose, vel, acc), wait(sec), set_payload(kg, cog)
  gripper: open(), grip() -> bool (보드 감지 여부)
"""

import time


# =============================================================================
# 로봇
# =============================================================================
class DryRunRobot:
    """로봇 없이 동작 순서만 출력."""

    def __init__(self, log=print):
        self.log = log

    def movej(self, joints, vel, acc):
        self.log(f"    movej {joints}  vel={vel:.1f}")

    def movel(self, pose, vel, acc):
        self.log(f"    movel {pose[:3]}  vel={[round(v, 1) for v in vel]}")

    def wait(self, sec):
        pass

    def set_payload(self, kg, cog):
        self.log(f"    payload {kg}kg")


class DsrRobot:
    """두산 DSR_ROBOT2 어댑터. connect_dsr() 로 만든다."""

    def __init__(self, dsr, common, log=print):
        self.dsr, self.c, self.log = dsr, common, log

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

    def set_payload(self, kg, cog):
        # 들고 있는 보드 무게를 로봇에 알려 충돌 감지·제어 정확도를 유지한다.
        # 두산 펌웨어/패키지 버전에 따라 함수가 없을 수 있어 그때는 경고만 남긴다.
        fn = getattr(self.dsr, "set_workpiece_weight", None)
        if fn is None:
            self.log(f"[경고] set_workpiece_weight 를 찾을 수 없어 페이로드({kg}kg)를 설정하지 못했습니다")
            return
        self._check(fn(weight=kg, cog=list(cog)), "set_workpiece_weight")


def connect_dsr(robot_id, robot_model, log=print):
    """rclpy.init() 이후 호출. (DsrRobot, DSR_ROBOT2 모듈) 반환."""
    import rclpy
    import DR_init

    DR_init.__dsr__id = robot_id
    DR_init.__dsr__model = robot_model
    node = rclpy.create_node("farm3_robot_dsr", namespace=robot_id)
    DR_init.__dsr__node = node
    # DSR_ROBOT2 는 DR_init 에 노드를 등록한 뒤에 import 해야 한다
    import DR_common2
    import DSR_ROBOT2

    return DsrRobot(DSR_ROBOT2, DR_common2, log), DSR_ROBOT2


# =============================================================================
# 그리퍼 (OnRobot RG2)
# =============================================================================
class MockGripper:
    def __init__(self, log=print):
        self.log = log

    def open(self):
        self.log("    gripper open")

    def grip(self):
        self.log("    gripper grip (mock: 항상 감지)")
        return True


class OnRobotRG2Modbus:
    """OnRobot Compute Box Modbus TCP (pip install pymodbus). 단위 0.1mm / 0.1N.

    쓰기 0: 목표 힘, 1: 목표 폭, 2: 제어(16 = 오프셋 반영 이동)
    읽기 268: 상태 (bit0 동작 중, bit1 파지 감지)
    ※ 레지스터 번호는 OnRobot 매뉴얼에서 꼭 한 번 확인할 것
    """

    UNIT_ID = 65
    REG_FORCE, REG_STATUS, CTRL_MOVE = 0, 268, 16

    def __init__(self, ip, port, open_width, grip_width, force, timeout_sec=5.0):
        from pymodbus.client import ModbusTcpClient

        self.client = ModbusTcpClient(ip, port=port, timeout=2)
        if not self.client.connect():
            raise ConnectionError(f"OnRobot Compute Box({ip}:{port})에 연결할 수 없습니다")
        self.open_width, self.grip_width = open_width, grip_width
        self.force, self.timeout = force, timeout_sec

    def _call(self, fn, *args, **kwargs):
        # pymodbus 버전마다 장치 ID 인자 이름이 다르다
        for key in ("device_id", "slave", "unit"):
            try:
                return fn(*args, **kwargs, **{key: self.UNIT_ID})
            except TypeError:
                continue
        raise RuntimeError("지원하지 않는 pymodbus 버전입니다")

    def _move(self, width_mm):
        values = [int(self.force * 10), int(width_mm * 10), self.CTRL_MOVE]
        if self._call(self.client.write_registers, self.REG_FORCE, values).isError():
            raise RuntimeError("그리퍼 명령 전송 실패")
        time.sleep(0.1)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            rr = self._call(self.client.read_holding_registers, self.REG_STATUS, count=1)
            if rr.isError():
                raise RuntimeError("그리퍼 상태 읽기 실패")
            status = rr.registers[0]
            if not status & 0b01:
                return bool(status & 0b10)
            time.sleep(0.05)
        raise TimeoutError("그리퍼 동작이 제한 시간 안에 끝나지 않았습니다")

    def open(self):
        self._move(self.open_width)

    def grip(self):
        return self._move(self.grip_width)


class DsrIoGripper:
    """컨트롤러 디지털 출력으로 제어. 파지 감지가 없어서 grip() 은 항상 True."""

    def __init__(self, set_digital_output, wait, grip_pattern, release_pattern, settle_sec):
        self._set, self._wait = set_digital_output, wait
        self.grip_pattern = {int(k): int(v) for k, v in grip_pattern.items()}
        self.release_pattern = {int(k): int(v) for k, v in release_pattern.items()}
        self.settle = settle_sec

    def _apply(self, pattern):
        for pin, value in pattern.items():
            self._set(pin, value)
        self._wait(self.settle)

    def open(self):
        self._apply(self.release_pattern)

    def grip(self):
        self._apply(self.grip_pattern)
        return True


def make_gripper(gcfg, dsr=None, log=print):
    backend = gcfg["backend"]
    if backend == "mock":
        return MockGripper(log)
    if backend == "onrobot_modbus":
        return OnRobotRG2Modbus(gcfg["ip"], gcfg["port"], gcfg["open_width"], gcfg["grip_width"],
                                gcfg["force"], gcfg.get("timeout_sec", 5.0))
    if backend == "dsr_io":
        if dsr is None:
            raise ValueError("dsr_io 그리퍼는 실제 로봇 모드에서만 쓸 수 있습니다")
        io = gcfg["dsr_io"]
        return DsrIoGripper(dsr.set_digital_output, dsr.wait, io["grip"], io["release"], io["settle_sec"])
    raise ValueError(f"알 수 없는 그리퍼 backend: {backend}")
