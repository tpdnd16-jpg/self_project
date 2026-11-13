"""OnRobot RG2 그리퍼 제어.

backend
  mock           : 하드웨어 없이 테스트
  onrobot_modbus : OnRobot Compute Box에 Modbus TCP 직접 연결 (pip install pymodbus)
  dsr_io         : 두산 컨트롤러 디지털 출력으로 제어 (티치 펜던트에 RG2 I/O 매핑이 돼 있을 때)
"""

import time


class MockGripper:
    def __init__(self, log=print):
        self.log = log

    def open(self):
        self.log("[mock gripper] open")

    def grip(self):
        self.log("[mock gripper] grip -> 감지됨")
        return True


class OnRobotRG2Modbus:
    """OnRobot Compute Box Modbus TCP 레지스터 (RG2/RG6 공통, 단위 0.1mm / 0.1N).

    쓰기  0: 목표 힘, 1: 목표 폭, 2: 제어 (16 = 오프셋 반영 이동, 8 = 정지)
    읽기 268: 상태 비트 (bit0 = 동작 중, bit1 = 파지 감지)
    """

    UNIT_ID = 65
    REG_FORCE, REG_WIDTH, REG_CONTROL = 0, 1, 2
    REG_STATUS = 268
    CTRL_MOVE = 16

    def __init__(self, ip, port, open_width, grip_width, force, timeout_sec=5.0, log=print):
        from pymodbus.client import ModbusTcpClient

        self.client = ModbusTcpClient(ip, port=port, timeout=2)
        if not self.client.connect():
            raise ConnectionError(f"OnRobot Compute Box({ip}:{port})에 연결할 수 없습니다")
        self.open_width, self.grip_width = open_width, grip_width
        self.force, self.timeout = force, timeout_sec
        self.log = log

    def _call(self, fn, *args, **kwargs):
        # pymodbus 버전마다 장치 ID 인자 이름이 다르다 (device_id / slave / unit)
        for key in ("device_id", "slave", "unit"):
            try:
                return fn(*args, **kwargs, **{key: self.UNIT_ID})
            except TypeError:
                continue
        raise RuntimeError("지원하지 않는 pymodbus 버전입니다")

    def _status(self):
        rr = self._call(self.client.read_holding_registers, self.REG_STATUS, count=1)
        if rr.isError():
            raise RuntimeError(f"그리퍼 상태 읽기 실패: {rr}")
        return rr.registers[0]

    def _move(self, width_mm):
        values = [int(self.force * 10), int(width_mm * 10), self.CTRL_MOVE]
        wr = self._call(self.client.write_registers, self.REG_FORCE, values)
        if wr.isError():
            raise RuntimeError(f"그리퍼 명령 실패: {wr}")
        time.sleep(0.1)  # busy 비트가 올라올 시간
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            status = self._status()
            if not status & 0b01:          # 동작 완료
                return bool(status & 0b10)  # 파지 감지 여부
            time.sleep(0.05)
        raise TimeoutError("그리퍼 동작이 제한 시간 안에 끝나지 않았습니다")

    def open(self):
        self._move(self.open_width)

    def grip(self):
        return self._move(self.grip_width)


class DsrIoGripper:
    """두산 컨트롤러 디지털 출력으로 그리퍼를 제어. 파지 감지는 할 수 없어 항상 True."""

    def __init__(self, set_digital_output, wait, grip_pattern, release_pattern, settle_sec, log=print):
        self._set, self._wait = set_digital_output, wait
        self.grip_pattern = {int(k): int(v) for k, v in grip_pattern.items()}
        self.release_pattern = {int(k): int(v) for k, v in release_pattern.items()}
        self.settle = settle_sec
        self.log = log

    def _apply(self, pattern):
        for pin, value in pattern.items():
            self._set(pin, value)
        self._wait(self.settle)

    def open(self):
        self._apply(self.release_pattern)

    def grip(self):
        self._apply(self.grip_pattern)
        return True


def make_gripper(cfg, dsr=None, log=print):
    """cfg['gripper'] 설정으로 그리퍼 객체 생성. dsr_io 백엔드는 DSR_ROBOT2 모듈이 필요."""
    g = cfg["gripper"]
    backend = g["backend"]
    if backend == "mock":
        return MockGripper(log)
    if backend == "onrobot_modbus":
        return OnRobotRG2Modbus(
            g["ip"], g["port"], g["open_width"], g["grip_width"], g["force"],
            g.get("timeout_sec", 5.0), log,
        )
    if backend == "dsr_io":
        if dsr is None:
            raise ValueError("dsr_io 그리퍼는 실제 로봇 모드에서만 쓸 수 있습니다")
        io = g["dsr_io"]
        return DsrIoGripper(dsr.set_digital_output, dsr.wait, io["grip"], io["release"], io["settle_sec"], log)
    raise ValueError(f"알 수 없는 그리퍼 backend: {backend}")
