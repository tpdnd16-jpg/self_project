"""시퀀스 실행기. 로봇과 그리퍼를 주입받으므로 가짜 객체로 테스트할 수 있다."""


class GripError(RuntimeError):
    pass


class AbortRequested(RuntimeError):
    pass


class SequenceExecutor:
    def __init__(self, robot, gripper, motion_cfg, on_progress=None, should_abort=None):
        """
        robot   : movej(joints, vel, acc), movel(pose, vel, acc), wait(sec) 를 가진 객체
        gripper : open(), grip() -> bool(파지 감지) 를 가진 객체
        """
        self.robot = robot
        self.gripper = gripper
        self.m = motion_cfg
        self.on_progress = on_progress or (lambda i, total, step: None)
        self.should_abort = should_abort or (lambda: False)

    def run(self, steps):
        total = len(steps)
        for i, step in enumerate(steps, 1):
            # 중지 요청은 동작과 동작 사이에서만 반영한다 (동작 도중 정지는 비상정지 버튼으로)
            if self.should_abort():
                raise AbortRequested(f"{i}/{total} 단계 전에 중지 요청됨")
            self.on_progress(i, total, step)
            self._do(step)

    def _scaled(self, values):
        s = self.m["velocity_scale"]
        return [v * s for v in values]

    def _do(self, step):
        if step.kind == "movej":
            s = self.m["velocity_scale"]
            self.robot.movej(list(step.target), vel=self.m["joint_vel"] * s, acc=self.m["joint_acc"] * s)
        elif step.kind == "movel":
            self.robot.movel(
                list(step.target),
                vel=self._scaled(self.m[f"{step.speed}_vel"]),
                acc=self._scaled(self.m[f"{step.speed}_acc"]),
            )
        elif step.kind == "open":
            self.gripper.open()
        elif step.kind == "grip":
            if not self.gripper.grip():
                raise GripError(f"'{step.label}' 실패: 그리퍼에 플레이트가 감지되지 않았습니다")
        elif step.kind == "wait":
            self.robot.wait(step.seconds)
        else:
            raise ValueError(f"알 수 없는 단계 종류: {step.kind}")
