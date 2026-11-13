import copy
import os
import unittest

from farm3_robot.positions import ConfigError, LocationError, get_location, incomplete_ids, load_config, validate_config
from farm3_robot.tasks import WORK_TYPE_EJECT, WORK_TYPE_INSERT, TaskRunner, build_eject, build_insert

DEFAULT_CONFIG = os.path.join(os.path.dirname(__file__), "..", "config", "positions.yaml")

TOOL_DOWN = [0.0, 180.0, 0.0]


def filled_config():
    """기본 설정에 테스트용 좌표·무게를 채운 설정."""
    cfg = load_config(DEFAULT_CONFIG)
    cfg["payload"]["board_empty_kg"] = 0.5
    cfg["payload"]["board_printed_kg"] = 0.8
    cfg["stackers"][1].update(approach=[300.0, -400.0, 200.0] + TOOL_DOWN, target=[450.0, -400.0, 200.0] + TOOL_DOWN)
    cfg["stackers"][2].update(approach=[300.0, -400.0, 300.0] + TOOL_DOWN, target=[450.0, -400.0, 300.0] + TOOL_DOWN)
    cfg["printers"][1].update(approach=[350.0, 0.0, 250.0] + TOOL_DOWN, target=[560.0, 0.0, 180.0] + TOOL_DOWN)
    cfg["printers"][2].update(approach=[350.0, 300.0, 250.0] + TOOL_DOWN, target=[560.0, 300.0, 180.0] + TOOL_DOWN)
    cfg["receivers"][1].update(approach=[300.0, 400.0, 200.0] + TOOL_DOWN, target=[450.0, 400.0, 150.0] + TOOL_DOWN)
    validate_config(cfg)
    return cfg


class FakeRobot:
    def __init__(self):
        self.calls = []

    def movej(self, joints, vel, acc):
        self.calls.append(("movej", tuple(joints)))

    def movel(self, pose, vel, acc):
        self.calls.append(("movel", tuple(pose), tuple(vel)))

    def wait(self, sec):
        self.calls.append(("wait", sec))

    def set_payload(self, kg, cog):
        self.calls.append(("payload", kg))


class FakeGripper:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.events = []

    def open(self):
        self.events.append("open")

    def grip(self):
        self.events.append("grip")
        return self.results.pop(0) if self.results else True


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        self.t += 1.0
        return self.t


# ---------------------------------------------------------------------------
class TestConfig(unittest.TestCase):
    def test_default_config_loads_with_empty_positions(self):
        cfg = load_config(DEFAULT_CONFIG)
        self.assertEqual(incomplete_ids(cfg)["printers"], [1, 2])

    def test_filled_config_has_no_incomplete_ids_in_use(self):
        cfg = filled_config()
        self.assertEqual(incomplete_ids(cfg)["printers"], [])
        self.assertEqual(incomplete_ids(cfg)["stackers"], [3])

    def test_unknown_id_rejected(self):
        with self.assertRaises(LocationError) as ctx:
            get_location(filled_config(), "printers", 9)
        self.assertIn("9", str(ctx.exception))

    def test_empty_coordinate_rejected_on_use(self):
        with self.assertRaises(LocationError) as ctx:
            get_location(load_config(DEFAULT_CONFIG), "stackers", 1)
        self.assertIn("좌표", str(ctx.exception))

    def test_out_of_workspace_rejected(self):
        cfg = filled_config()
        cfg["printers"][1]["target"] = [560.0, 0.0, 10.0] + TOOL_DOWN
        with self.assertRaises(ConfigError):
            validate_config(cfg)

    def test_lifted_position_also_checked(self):
        cfg = filled_config()
        cfg["printers"][1]["target"] = [300.0, 0.0, 695.0] + TOOL_DOWN  # + lift_dz 15 → z 상한 초과
        with self.assertRaises(ConfigError):
            validate_config(cfg)

    def test_beyond_reach_rejected(self):
        cfg = filled_config()
        cfg["receivers"][1]["approach"] = [700.0, 700.0, 300.0] + TOOL_DOWN
        with self.assertRaises(ConfigError):
            validate_config(cfg)

    def test_id_out_of_int8_rejected(self):
        cfg = filled_config()
        cfg["printers"][200] = {"approach": None, "target": None, "lift_dz": 10.0}
        with self.assertRaises(ConfigError):
            validate_config(cfg)

    def test_bad_velocity_scale_rejected(self):
        cfg = filled_config()
        cfg["motion"]["velocity_scale"] = 0
        with self.assertRaises(ConfigError):
            validate_config(cfg)


# ---------------------------------------------------------------------------
def _home_indices(steps):
    return [i for i, s in enumerate(steps) if s.kind == "movej"]


class TestSequences(unittest.TestCase):
    def setUp(self):
        self.cfg = filled_config()

    def _check_flow(self, steps):
        kinds = [s.kind for s in steps]
        grip_i, release_i = kinds.index("grip"), len(kinds) - 1 - kinds[::-1].index("open")
        homes = _home_indices(steps)
        self.assertEqual(homes[0], 0, "홈에서 시작")
        self.assertEqual(homes[-1], len(steps) - 1, "홈에서 끝")
        self.assertTrue(any(grip_i < h < release_i for h in homes), "집은 뒤 놓기 전에 홈을 거쳐야 함")
        return grip_i, release_i

    def test_insert_flow_stacker_home_printer_home(self):
        steps = build_insert(self.cfg, start_pos_id=1, printer_pos_id=2)
        grip_i, release_i = self._check_flow(steps)
        stacker, printer = self.cfg["stackers"][1], self.cfg["printers"][2]
        before = {s.target for s in steps[:grip_i]}
        after = {s.target for s in steps[grip_i:release_i]}
        self.assertIn(tuple(stacker["target"]), before)
        self.assertIn(tuple(printer["target"]), after)

    def test_eject_flow_printer_home_receiver_home(self):
        steps = build_eject(self.cfg, printer_pos_id=1, receive_pos_id=1)
        grip_i, release_i = self._check_flow(steps)
        self.assertIn(tuple(self.cfg["printers"][1]["target"]), {s.target for s in steps[:grip_i]})
        self.assertIn(tuple(self.cfg["receivers"][1]["target"]), {s.target for s in steps[grip_i:release_i]})

    def test_via_home_can_be_disabled(self):
        self.cfg["motion"]["via_home"]["eject"] = False
        steps = build_eject(self.cfg, 1, 1)
        self.assertEqual(len(_home_indices(steps)), 2)

    def test_pick_lifts_straight_up_then_backs_out(self):
        steps = build_insert(self.cfg, 1, 1)
        loc = self.cfg["stackers"][1]
        i = [s.kind for s in steps].index("grip")
        lift, out = steps[i + 2], steps[i + 3]  # grip, payload, lift, back-out
        self.assertEqual(lift.target[:2], tuple(loc["target"][:2]))
        self.assertEqual(lift.target[2], loc["target"][2] + loc["lift_dz"])
        self.assertEqual(out.target[2], loc["approach"][2] + loc["lift_dz"])

    def test_place_lowers_onto_target_before_release(self):
        steps = build_insert(self.cfg, 1, 1)
        kinds = [s.kind for s in steps]
        release_i = len(kinds) - 1 - kinds[::-1].index("open")
        last_move = [s for s in steps[:release_i] if s.kind == "movel"][-1]
        self.assertEqual(last_move.target, tuple(self.cfg["printers"][1]["target"]))
        self.assertEqual(last_move.speed, "fine")

    def test_payload_weights(self):
        ins = [s.value for s in build_insert(self.cfg, 1, 1) if s.kind == "payload"]
        ej = [s.value for s in build_eject(self.cfg, 1, 1) if s.kind == "payload"]
        self.assertEqual(ins, [0.5, 0.0])
        self.assertEqual(ej, [0.8, 0.0])


# ---------------------------------------------------------------------------
class TestTaskRunner(unittest.TestCase):
    def setUp(self):
        self.cfg = filled_config()
        self.robot, self.gripper = FakeRobot(), FakeGripper()
        self.runner = TaskRunner(self.cfg, self.robot, self.gripper, clock=FakeClock())

    def test_insert_success_result_matches_interface(self):
        feedback = []
        res = self.runner.insert(work_id=7, start_pos_id=1, printer_pos_id=1, feedback_cb=feedback.append)
        self.assertEqual(res, {"success": True, "message": res["message"], "work_id": 7, "work_type": WORK_TYPE_INSERT})
        self.assertEqual(self.gripper.events, ["open", "grip", "open"])
        self.assertEqual(set(feedback[0]), {"start_at", "end_at", "work_id", "step", "total", "phase"})
        self.assertEqual(feedback[0]["end_at"], 0.0)
        self.assertGreater(feedback[-1]["end_at"], feedback[-1]["start_at"])
        self.assertEqual(feedback[-1]["step"], feedback[-1]["total"])
        self.assertTrue(all(f["work_id"] == 7 for f in feedback))

    def test_eject_success(self):
        res = self.runner.eject(work_id=8, printer_pos_id=1, receive_pos_id=1)
        self.assertTrue(res["success"])
        self.assertEqual(res["work_type"], WORK_TYPE_EJECT)

    def test_grip_failure_stops_robot(self):
        runner = TaskRunner(self.cfg, self.robot, FakeGripper([False]), clock=FakeClock())
        res = runner.eject(work_id=3, printer_pos_id=1, receive_pos_id=1)
        self.assertFalse(res["success"])
        self.assertIn("감지", res["message"])
        self.assertEqual(self.robot.calls[-1][0], "wait", "파지 실패 후 추가 이동 없음")

    def test_empty_coordinate_rejected_before_moving(self):
        res = self.runner.insert(work_id=1, start_pos_id=3, printer_pos_id=1)  # 적재대 3번 좌표 없음
        self.assertFalse(res["success"])
        self.assertIn("stackers 3", res["message"])
        self.assertEqual(self.robot.calls, [])

    def test_missing_weight_rejected_before_moving(self):
        self.cfg["payload"]["board_printed_kg"] = None
        res = self.runner.eject(work_id=1, printer_pos_id=1, receive_pos_id=1)
        self.assertFalse(res["success"])
        self.assertIn("무게", res["message"])
        self.assertEqual(self.robot.calls, [])

    def test_missing_weight_allowed_in_dry_run(self):
        self.cfg["payload"]["board_printed_kg"] = None
        runner = TaskRunner(self.cfg, self.robot, self.gripper, clock=FakeClock(), dry_run=True)
        self.assertTrue(runner.eject(work_id=1, printer_pos_id=1, receive_pos_id=1)["success"])

    def test_stop_request_between_steps(self):
        def fb(f):
            if f["step"] == 3:
                self.runner.request_stop()

        res = self.runner.insert(work_id=1, start_pos_id=1, printer_pos_id=1, feedback_cb=fb)
        self.assertFalse(res["success"])
        self.assertIn("중지", res["message"])

    def test_busy_runner_rejects_second_task(self):
        def fb(f):
            if f["step"] == 1:
                inner.append(self.runner.eject(work_id=2, printer_pos_id=1, receive_pos_id=1))

        inner = []
        res = self.runner.insert(work_id=1, start_pos_id=1, printer_pos_id=1, feedback_cb=fb)
        self.assertTrue(res["success"])
        self.assertFalse(inner[0]["success"])
        self.assertIn("작업 중", inner[0]["message"])

    def test_robot_error_reported(self):
        def boom(*a, **k):
            raise RuntimeError("알람 발생")

        self.robot.movel = boom
        res = self.runner.insert(work_id=5, start_pos_id=1, printer_pos_id=1)
        self.assertFalse(res["success"])
        self.assertIn("알람 발생", res["message"])
        self.assertEqual(res["work_id"], 5)


if __name__ == "__main__":
    unittest.main()
