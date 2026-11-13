import copy
import os
import unittest

from printer_plate_swap.config import ConfigError, load_config, validate_config
from printer_plate_swap.executor import AbortRequested, GripError, SequenceExecutor
from printer_plate_swap.sequence import RackTracker, build_swap_sequence

CONFIG = os.path.join(os.path.dirname(__file__), "..", "config", "plate_swap.yaml")


class FakeRobot:
    def __init__(self):
        self.calls = []

    def movej(self, joints, vel, acc):
        self.calls.append(("movej", tuple(joints), vel))

    def movel(self, pose, vel, acc):
        self.calls.append(("movel", tuple(pose), tuple(vel)))

    def wait(self, sec):
        self.calls.append(("wait", sec))


class FakeGripper:
    def __init__(self, grip_results=None):
        self.events = []
        self.grip_results = list(grip_results or [])

    def open(self):
        self.events.append("open")

    def grip(self):
        self.events.append("grip")
        return self.grip_results.pop(0) if self.grip_results else True


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(CONFIG)

    def test_default_config_is_valid(self):
        validate_config(self.cfg)

    def test_rejects_pose_out_of_workspace(self):
        bad = copy.deepcopy(self.cfg)
        bad["poses"]["plate_grip"][2] = 10.0  # 작업대 아래
        with self.assertRaises(ConfigError):
            validate_config(bad)

    def test_rejects_pose_beyond_reach(self):
        bad = copy.deepcopy(self.cfg)
        bad["racks"]["fresh"][0] = [700.0, -700.0, 150.0, 0.0, 180.0, 0.0]
        with self.assertRaises(ConfigError):
            validate_config(bad)

    def test_rejects_approach_above_z_limit(self):
        bad = copy.deepcopy(self.cfg)
        bad["poses"]["printer_front"][2] = 690.0  # +approach_dz 하면 Z 상한 초과
        with self.assertRaises(ConfigError):
            validate_config(bad)

    def test_rejects_bad_velocity_scale(self):
        for scale in (0, 1.5):
            bad = copy.deepcopy(self.cfg)
            bad["motion"]["velocity_scale"] = scale
            with self.assertRaises(ConfigError):
                validate_config(bad)

    def test_rejects_empty_rack(self):
        bad = copy.deepcopy(self.cfg)
        bad["racks"]["done"] = []
        with self.assertRaises(ConfigError):
            validate_config(bad)

    def test_rejects_unknown_gripper_backend(self):
        bad = copy.deepcopy(self.cfg)
        bad["gripper"]["backend"] = "magic"
        with self.assertRaises(ConfigError):
            validate_config(bad)

    def test_rejects_malformed_pose(self):
        bad = copy.deepcopy(self.cfg)
        bad["poses"]["plate_out"] = [400.0, 0.0, 195.0]
        with self.assertRaises(ConfigError):
            validate_config(bad)


class TestSequence(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(CONFIG)
        self.steps = build_swap_sequence(self.cfg, 0, 0)

    def test_starts_and_ends_at_home(self):
        home = tuple(self.cfg["poses"]["home_j"])
        self.assertEqual((self.steps[0].kind, self.steps[0].target), ("movej", home))
        self.assertEqual((self.steps[-1].kind, self.steps[-1].target), ("movej", home))

    def test_gripper_order(self):
        # 열기 → (사용 플레이트) 잡기 → 놓기 → (새 플레이트) 잡기 → 놓기
        kinds = [s.kind for s in self.steps if s.kind in ("open", "grip")]
        self.assertEqual(kinds, ["open", "grip", "open", "grip", "open"])

    def test_grip_and_release_happen_at_slow_speed_positions(self):
        for i, s in enumerate(self.steps):
            if s.kind in ("grip", "open") and i > 2:
                prev_move = next(p for p in reversed(self.steps[:i]) if p.kind == "movel")
                self.assertEqual(prev_move.speed, "fine", f"{s.label} 직전 이동은 저속이어야 합니다")

    def test_uses_requested_rack_slots(self):
        steps = build_swap_sequence(self.cfg, 1, 1)
        targets = {s.target for s in steps if s.kind == "movel"}
        self.assertIn(tuple(self.cfg["racks"]["done"][1]), targets)
        self.assertIn(tuple(self.cfg["racks"]["fresh"][1]), targets)
        self.assertNotIn(tuple(self.cfg["racks"]["done"][0]), targets)

    def test_printer_entered_and_left_via_front(self):
        front = tuple(self.cfg["poses"]["printer_front"])
        grip_i = [i for i, s in enumerate(self.steps) if s.target == tuple(self.cfg["poses"]["plate_grip"])]
        for i in grip_i:
            before = [s.target for s in self.steps[:i] if s.kind == "movel"]
            self.assertIn(front, before)

    def test_plate_is_lifted_before_pulling_out(self):
        grip = self.cfg["poses"]["plate_grip"]
        idx = next(i for i, s in enumerate(self.steps) if s.kind == "grip")
        lift = self.steps[idx + 1]
        self.assertEqual(lift.target[2], grip[2] + self.cfg["motion"]["peel_dz"])
        self.assertEqual(lift.target[:2], tuple(grip[:2]))


class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(CONFIG)
        self.steps = build_swap_sequence(self.cfg, 0, 0)

    def test_runs_all_steps_with_scaled_speed(self):
        robot, gripper = FakeRobot(), FakeGripper()
        progress = []
        SequenceExecutor(robot, gripper, self.cfg["motion"], lambda i, n, s: progress.append(i)).run(self.steps)
        self.assertEqual(progress, list(range(1, len(self.steps) + 1)))
        self.assertEqual(gripper.events, ["open", "grip", "open", "grip", "open"])
        scale = self.cfg["motion"]["velocity_scale"]
        fine = [v * scale for v in self.cfg["motion"]["fine_vel"]]
        self.assertIn(tuple(fine), {c[2] for c in robot.calls if c[0] == "movel"})

    def test_stops_when_grip_not_detected(self):
        robot, gripper = FakeRobot(), FakeGripper(grip_results=[False])
        with self.assertRaises(GripError):
            SequenceExecutor(robot, gripper, self.cfg["motion"]).run(self.steps)
        # 파지 실패 후에는 더 이상 움직이지 않아야 한다 (들어올리기 이동 없음)
        last_move = [c for c in robot.calls if c[0] == "movel"][-1]
        self.assertEqual(last_move[1], tuple(self.cfg["poses"]["plate_grip"]))
        self.assertEqual(robot.calls[-1][0], "wait")
        self.assertEqual(gripper.events, ["open", "grip"])

    def test_abort_between_steps(self):
        robot, gripper = FakeRobot(), FakeGripper()
        count = {"n": 0}

        def should_abort():
            count["n"] += 1
            return count["n"] > 3

        with self.assertRaises(AbortRequested):
            SequenceExecutor(robot, gripper, self.cfg["motion"], should_abort=should_abort).run(self.steps)
        self.assertEqual(len(robot.calls) + len(gripper.events), 3)


class TestRackTracker(unittest.TestCase):
    def test_advances_only_on_commit(self):
        t = RackTracker(2, 2)
        self.assertEqual(t.next_slots()[0], (0, 0))
        self.assertEqual(t.next_slots()[0], (0, 0))  # commit 전에는 그대로
        t.commit()
        self.assertEqual(t.next_slots()[0], (1, 1))

    def test_reports_full_and_reset(self):
        t = RackTracker(1, 3)
        t.commit()
        slots, reason = t.next_slots()
        self.assertIsNone(slots)
        self.assertIn("완료 랙", reason)
        t.reset()
        self.assertEqual(t.next_slots()[0], (0, 0))

    def test_reports_empty_fresh_rack(self):
        t = RackTracker(3, 1)
        t.commit()
        slots, reason = t.next_slots()
        self.assertIsNone(slots)
        self.assertIn("새 플레이트", reason)


if __name__ == "__main__":
    unittest.main()
