"""단독 실행 도구 (통신 없이 로봇 동작만 확인).

  # 로봇 없이 순서 확인 (ROS 불필요, 좌표·무게가 비어 있어도 가능한 범위까지)
  ros2 run farm3_robot run_task insert --work-id 1 --start-pos 1 --printer-pos 1 --dry-run
  ros2 run farm3_robot run_task eject  --work-id 2 --printer-pos 1 --receive-pos 1 --dry-run

  # 실제 로봇 (두산 드라이버 실행 중이어야 함)
  ros2 run farm3_robot run_task insert --work-id 1 --start-pos 1 --printer-pos 1

  # 좌표가 비어 있는 ID 확인
  ros2 run farm3_robot run_task check
"""

import argparse
import os
import sys
from datetime import datetime

from .positions import ConfigError, incomplete_ids, load_config
from .robot_io import DryRunRobot, MockGripper, connect_dsr, make_gripper
from .tasks import TaskRunner


def default_config_path():
    try:
        from ament_index_python.packages import get_package_share_directory

        return os.path.join(get_package_share_directory("farm3_robot"), "config", "positions.yaml")
    except Exception:
        return os.path.join(os.path.dirname(__file__), "..", "config", "positions.yaml")


def parse_args(argv):
    p = argparse.ArgumentParser(prog="run_task", description="3D 프린터 보드 투입/회수 로봇 동작")
    p.add_argument("--config", default=default_config_path(), help="positions.yaml 경로")
    sub = p.add_subparsers(dest="task", required=True)

    ins = sub.add_parser("insert", help="적재대 → 프린터 보드 투입")
    ins.add_argument("--work-id", type=int, required=True)
    ins.add_argument("--start-pos", type=int, required=True, help="적재대 ID (start_pos_id)")
    ins.add_argument("--printer-pos", type=int, required=True, help="프린터 ID (printer_pos_id)")

    ej = sub.add_parser("eject", help="프린터 → 수령대 보드 회수")
    ej.add_argument("--work-id", type=int, required=True)
    ej.add_argument("--printer-pos", type=int, required=True, help="프린터 ID (printer_pos_id)")
    ej.add_argument("--receive-pos", type=int, required=True, help="수령대 ID (receive_pos_id)")

    for sp in (ins, ej):
        sp.add_argument("--dry-run", action="store_true", help="로봇 없이 순서만 출력")
    sub.add_parser("check", help="좌표가 비어 있는 위치 ID 출력")
    return p.parse_args(argv)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # ros2 run 이 붙이는 --ros-args 이후 인자는 무시
    if "--ros-args" in argv:
        argv = argv[: argv.index("--ros-args")]
    args = parse_args(argv)

    try:
        cfg = load_config(args.config)
    except (OSError, ConfigError) as e:
        print(f"[오류] 설정 파일 ({args.config}): {e}")
        return 1

    if args.task == "check":
        for kind, ids in incomplete_ids(cfg).items():
            print(f"{kind:10s} 좌표 미입력 ID: {ids if ids else '없음'}")
        for key in ("board_empty_kg", "board_printed_kg"):
            print(f"payload.{key}: {cfg['payload'][key] if cfg['payload'][key] is not None else '미입력'}")
        return 0

    rclpy = None
    if args.dry_run:
        robot, gripper = DryRunRobot(), MockGripper()
        dsr = None
    else:
        import rclpy

        rclpy.init()
        try:
            robot, dsr = connect_dsr(cfg["robot"]["id"], cfg["robot"]["model"])
            gripper = make_gripper(cfg["gripper"], dsr=dsr)
        except Exception as e:
            print(f"[오류] 로봇/그리퍼 연결 실패: {e}")
            rclpy.shutdown()
            return 1

    runner = TaskRunner(cfg, robot, gripper, dry_run=args.dry_run, log=print)

    def on_feedback(fb):
        if fb["end_at"]:
            print(f"  ▶ 종료 {datetime.fromtimestamp(fb['end_at']):%H:%M:%S}")

    try:
        if args.task == "insert":
            res = runner.insert(args.work_id, args.start_pos, args.printer_pos, on_feedback)
        else:
            res = runner.eject(args.work_id, args.printer_pos, args.receive_pos, on_feedback)
    except KeyboardInterrupt:
        runner.request_stop()
        res = {"success": False, "message": "사용자 중단"}
    finally:
        if rclpy is not None:
            rclpy.shutdown()

    print(f"\n결과: {res}")
    return 0 if res["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
