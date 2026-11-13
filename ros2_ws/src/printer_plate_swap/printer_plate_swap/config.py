"""설정 파일 로드와 검증 (ROS 의존 없음)."""

import math

import yaml

POSE_NAMES = ("printer_front", "plate_grip", "plate_out")
GRIPPER_BACKENDS = ("mock", "onrobot_modbus", "dsr_io")


class ConfigError(ValueError):
    pass


def load_config(path):
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    validate_config(cfg)
    return cfg


def offset_z(pose, dz):
    p = list(pose)
    p[2] += dz
    return p


def _require(cfg, key, where="설정"):
    if not isinstance(cfg, dict) or key not in cfg:
        raise ConfigError(f"{where}에 '{key}' 항목이 없습니다")
    return cfg[key]


def _check_numbers(name, values, length):
    if not isinstance(values, (list, tuple)) or len(values) != length:
        raise ConfigError(f"{name}: 숫자 {length}개가 필요합니다 (받은 값: {values})")
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ConfigError(f"{name}: 숫자가 아닌 값이 있습니다 ({v!r})")


def check_pose(name, pose, ws):
    """작업 좌표가 안전 영역·도달 거리 안에 있는지 확인."""
    _check_numbers(name, pose, 6)
    for axis, value in zip("xyz", pose[:3]):
        low, high = ws[axis]
        if not low <= value <= high:
            raise ConfigError(f"{name}: {axis}={value} 가 안전 범위 [{low}, {high}] 밖입니다")
    x, y, z = pose[:3]
    reach = math.sqrt(x * x + y * y + (z - ws["base_height"]) ** 2)
    if reach > ws["max_reach"]:
        raise ConfigError(f"{name}: 도달 거리 {reach:.0f}mm 가 한계 {ws['max_reach']}mm 를 넘습니다")


def validate_config(cfg):
    motion = _require(cfg, "motion")
    ws = _require(cfg, "workspace")
    poses = _require(cfg, "poses")
    racks = _require(cfg, "racks")
    gripper = _require(cfg, "gripper")
    _require(cfg, "robot")

    for axis in "xyz":
        _check_numbers(f"workspace.{axis}", _require(ws, axis, "workspace"), 2)
    for key in ("max_reach", "base_height"):
        _require(ws, key, "workspace")

    scale = _require(motion, "velocity_scale", "motion")
    if not 0 < scale <= 1:
        raise ConfigError(f"motion.velocity_scale={scale} 는 0 초과 1 이하여야 합니다")
    for key in ("joint_vel", "joint_acc", "approach_dz", "peel_dz", "settle_sec"):
        if _require(motion, key, "motion") < 0:
            raise ConfigError(f"motion.{key} 는 음수일 수 없습니다")
    for key in ("travel_vel", "travel_acc", "fine_vel", "fine_acc"):
        _check_numbers(f"motion.{key}", _require(motion, key, "motion"), 2)

    _check_numbers("poses.home_j", _require(poses, "home_j", "poses"), 6)

    dz = motion["approach_dz"]
    for name in POSE_NAMES:
        pose = _require(poses, name, "poses")
        check_pose(name, pose, ws)
        check_pose(f"{name}(+접근 높이)", offset_z(pose, dz), ws)
    check_pose("plate_grip(+peel)", offset_z(poses["plate_grip"], motion["peel_dz"]), ws)

    for rack in ("done", "fresh"):
        slots = _require(racks, rack, "racks")
        if not isinstance(slots, list) or not slots:
            raise ConfigError(f"racks.{rack}: 슬롯이 최소 1개 필요합니다")
        for i, slot in enumerate(slots):
            check_pose(f"racks.{rack}[{i}]", slot, ws)
            check_pose(f"racks.{rack}[{i}](+접근 높이)", offset_z(slot, dz), ws)

    backend = _require(gripper, "backend", "gripper")
    if backend not in GRIPPER_BACKENDS:
        raise ConfigError(f"gripper.backend='{backend}' 는 {GRIPPER_BACKENDS} 중 하나여야 합니다")
    if not 0 <= gripper.get("open_width", 0) <= 110:
        raise ConfigError("gripper.open_width 는 0~110mm (RG2 범위) 여야 합니다")
    if not 0 <= gripper.get("force", 0) <= 40:
        raise ConfigError("gripper.force 는 0~40N (RG2 범위) 여야 합니다")
