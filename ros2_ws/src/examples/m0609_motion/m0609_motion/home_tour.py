"""M0609: 홈 → P1~P4 순회 → 홈 복귀.

각 목표 위치에서의 동작
  1) 접근 높이(목표 +100mm)로 직선 이동
  2) 목표 지점으로 저속 수직 하강
  3) 실제 위치를 읽어 목표와의 오차 확인
  4) 접근 높이로 수직 상승
전체 순회가 끝나거나 중간에 오류가 나면 홈으로 복귀한다.

실행 (두산 드라이버가 떠 있는 상태에서):
  ros2 run m0609_motion home_tour
"""

import rclpy
import DR_init

from m0609_motion import waypoints as wp

ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"

DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL


def main(args=None):
    rclpy.init(args=args)
    node = rclpy.create_node("m0609_home_tour", namespace=ROBOT_ID)
    DR_init.__dsr__node = node
    log = node.get_logger()

    try:
        # DSR_ROBOT2는 DR_init에 노드를 등록한 뒤에 import 해야 한다
        from DSR_ROBOT2 import movej, movel, get_current_posx, wait, DR_BASE
        from DR_common2 import posj, posx
    except ImportError as e:
        log.error(f"두산 ROS 2 패키지(DSR_ROBOT2)를 불러오지 못했습니다: {e}")
        rclpy.shutdown()
        return

    # 움직이기 전에 모든 좌표를 검증한다. 하나라도 범위를 벗어나면 로봇을 움직이지 않는다.
    try:
        wp.validate_all()
    except ValueError as e:
        log.error(f"좌표 검증 실패, 모션을 시작하지 않습니다: {e}")
        rclpy.shutdown()
        return

    home = posj(*wp.HOME_J)

    def go_home():
        log.info("홈 위치로 이동")
        movej(home, vel=wp.JOINT_VEL, acc=wp.JOINT_ACC)

    results = {}
    try:
        go_home()

        for name, target in wp.TARGETS.items():
            above = wp.approach_of(target)

            log.info(f"[{name}] 접근 위치로 이동: {above[:3]}")
            movel(posx(*above), vel=wp.TRAVEL_VEL, acc=wp.TRAVEL_ACC, ref=DR_BASE)

            log.info(f"[{name}] 목표 위치로 하강: {target[:3]}")
            movel(posx(*target), vel=wp.FINE_VEL, acc=wp.FINE_ACC, ref=DR_BASE)
            wait(0.5)  # 정지 후 위치 안정화

            actual, _sol = get_current_posx(ref=DR_BASE)
            err = wp.position_error(target, actual)
            results[name] = err
            status = "OK" if err <= wp.POSITION_TOLERANCE_MM else "허용 오차 초과"
            log.info(
                f"[{name}] 도착 실제 위치 {[round(v, 2) for v in actual[:3]]}, "
                f"오차 {err:.3f}mm ({status})"
            )

            log.info(f"[{name}] 접근 위치로 상승")
            movel(posx(*above), vel=wp.TRAVEL_VEL, acc=wp.TRAVEL_ACC, ref=DR_BASE)

        go_home()

        log.info("===== 순회 결과 =====")
        for name, err in results.items():
            mark = "OK" if err <= wp.POSITION_TOLERANCE_MM else "NG"
            log.info(f"  {name}: 오차 {err:.3f}mm [{mark}]")

    except Exception as e:  # 통신 오류, 로봇 알람 등
        log.error(f"모션 중 오류 발생: {e}")
        try:
            go_home()
        except Exception as home_err:
            log.error(f"홈 복귀 실패, 티치 펜던트로 로봇 상태를 확인하세요: {home_err}")
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
