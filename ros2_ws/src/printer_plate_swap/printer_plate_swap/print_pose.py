"""좌표 교시 도우미.

티치 펜던트의 직접 교시(Direct Teaching)로 로봇을 원하는 위치에 옮겨 놓고 Enter 를 누르면
현재 작업 좌표·관절 좌표를 plate_swap.yaml 에 바로 붙여 넣을 수 있는 형식으로 출력한다.

  ros2 run printer_plate_swap print_pose
"""

import rclpy
import DR_init

ROBOT_ID, ROBOT_MODEL = "dsr01", "m0609"


def _fmt(values):
    return "[" + ", ".join(f"{v:.1f}" for v in values) + "]"


def main(args=None):
    rclpy.init(args=args)
    DR_init.__dsr__id, DR_init.__dsr__model = ROBOT_ID, ROBOT_MODEL
    node = rclpy.create_node("print_pose", namespace=ROBOT_ID)
    DR_init.__dsr__node = node
    from DSR_ROBOT2 import DR_BASE, get_current_posj, get_current_posx

    names = ["home_j(관절)", "printer_front", "plate_grip", "plate_out",
             "racks.done[0]", "racks.done[1]", "racks.fresh[0]", "racks.fresh[1]"]
    print("로봇을 각 위치로 옮긴 뒤 Enter (종료: q + Enter)\n")
    try:
        i = 0
        while True:
            hint = names[i] if i < len(names) else f"추가 위치 {i + 1}"
            if input(f"[{hint}] 위치에서 Enter > ").strip().lower() == "q":
                break
            posx, _sol = get_current_posx(ref=DR_BASE)
            posj = get_current_posj()
            print(f"  작업 좌표: {_fmt(posx)}")
            print(f"  관절 좌표: {_fmt(posj)}\n")
            i += 1
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
