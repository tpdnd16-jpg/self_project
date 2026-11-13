import unittest

from m0609_motion import waypoints as wp


class TestWaypoints(unittest.TestCase):
    def test_four_targets_defined(self):
        self.assertEqual(list(wp.TARGETS), ["P1", "P2", "P3", "P4"])

    def test_all_default_targets_are_safe(self):
        wp.validate_all()  # 예외가 나지 않아야 한다

    def test_approach_is_directly_above(self):
        target = wp.TARGETS["P1"]
        above = wp.approach_of(target)
        self.assertEqual(above[:2], target[:2])
        self.assertEqual(above[2], target[2] + wp.APPROACH_OFFSET_Z)
        self.assertEqual(above[3:], target[3:])
        self.assertEqual(target[2], wp.TARGET_Z)  # 원본은 변경되지 않음

    def test_rejects_point_outside_workspace(self):
        with self.assertRaises(ValueError):
            wp.validate_pose("bad", [450.0, 0.0, 50.0, 0.0, 180.0, 0.0])  # 너무 낮음

    def test_rejects_point_beyond_reach(self):
        with self.assertRaises(ValueError):
            wp.validate_pose("far", [750.0, 400.0, 600.0, 0.0, 180.0, 0.0])

    def test_rejects_wrong_length(self):
        with self.assertRaises(ValueError):
            wp.validate_pose("short", [450.0, 0.0, 200.0])

    def test_rejects_unsafe_approach(self):
        # 목표는 안전해도 접근 높이(+100)가 Z 상한을 넘으면 거부
        with self.assertRaises(ValueError):
            wp.validate_all({"high": [450.0, 0.0, 550.0, 0.0, 180.0, 0.0]})

    def test_rejects_empty_targets(self):
        with self.assertRaises(ValueError):
            wp.validate_all({})

    def test_position_error(self):
        self.assertAlmostEqual(
            wp.position_error([0, 0, 0, 0, 0, 0], [3, 4, 0, 10, 10, 10]), 5.0
        )


if __name__ == "__main__":
    unittest.main()
