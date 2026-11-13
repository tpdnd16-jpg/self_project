"""설정 로드·검증과 위치 ID → 좌표 조회 (ROS 의존 없음).

좌표가 아직 비어 있는(null) ID 는 설정 로드 시에는 허용하고,
그 ID 를 실제 작업에 쓰려고 할 때 LocationError 로 거부한다.
"""

import math

import yaml

LOCATION_KINDS = ("stackers", "printers", "receivers")
KIND_LABEL = {"stackers": "적재대", "printers": "프린터", "receivers": "수령대"}
GRIPPER_BACKENDS = ("mock", "onrobot_modbus", "dsr_io")


class ConfigError(ValueError):
    """설정 파일 자체가 잘못됨 (노드 시작 불가)."""


class LocationError(ValueError):
    """요청한 위치 ID 를 쓸 수 없음 (해당 작업만 거부)."""


def load_config(path):
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    validate_config(cfg)
    return cfg


def lifted(pose, dz):
    p = list(pose)
    p[2] += dz
    return p


# ---------------------------------------------------------------------------
def _require(d, key, where):
    if not isinstance(d, dict) or key not in d:
        raise ConfigError(f"{where} 에 '{key}' 항목이 없습니다")
    return d[key]


def _check_numbers(name, values, length):
    if not isinstance(values, (list, tuple)) or len(values) != length:
        raise ConfigError(f"{name}: 숫자 {length}개가 필요합니다 (받은 값: {values})")
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ConfigError(f"{name}: 숫자가 아닌 값이 있습니다 ({v!r})")


def check_pose(name, pose, ws):
    """작업 좌표가 안전 영역·도달 거리 안인지 확인."""
    _check_numbers(name, pose, 6)
    for axis, value in zip("xyz", pose[:3]):
        low, high = ws[axis]
        if not low <= value <= high:
            raise ConfigError(f"{name}: {axis}={value} 가 안전 범위 [{low}, {high}] 밖입니다")
    x, y, z = pose[:3]
    reach = math.sqrt(x * x + y * y + (z - ws["base_height"]) ** 2)
    if reach > ws["max_reach"]:
        raise ConfigError(f"{name}: 도달 거리 {reach:.0f}mm 가 한계 {ws['max_reach']}mm 를 넘습니다")


def _check_location(kind, loc_id, loc, ws):
    name = f"{kind} {loc_id}"
    if not isinstance(loc_id, int) or isinstance(loc_id, bool) or not -128 <= loc_id <= 127:
        raise ConfigError(f"{kind}: ID '{loc_id}' 는 int8 범위(-128~127)의 정수여야 합니다")
    if not isinstance(loc, dict):
        raise ConfigError(f"{name}: approach / target / lift_dz 항목이 필요합니다")
    dz = _require(loc, "lift_dz", name)
    if isinstance(dz, bool) or not isinstance(dz, (int, float)) or dz < 0:
        raise ConfigError(f"{name}: lift_dz 는 0 이상의 숫자여야 합니다")
    for key in ("approach", "target"):
        pose = _require(loc, key, name)
        if pose is None:
            continue  # 아직 교시 전. 사용할 때 거부
        check_pose(f"{name}.{key}", pose, ws)
        check_pose(f"{name}.{key}(+lift_dz)", lifted(pose, dz), ws)


def validate_config(cfg):
    for key in ("robot", "home_j", "motion", "payload", "gripper", "workspace") + LOCATION_KINDS:
        _require(cfg, key, "설정")

    ws = cfg["workspace"]
    for axis in "xyz":
        _check_numbers(f"workspace.{axis}", _require(ws, axis, "workspace"), 2)
    _require(ws, "max_reach", "workspace")
    _require(ws, "base_height", "workspace")

    _check_numbers("home_j", cfg["home_j"], 6)

    m = cfg["motion"]
    scale = _require(m, "velocity_scale", "motion")
    if not 0 < scale <= 1:
        raise ConfigError(f"motion.velocity_scale={scale} 는 0 초과 1 이하여야 합니다")
    for key in ("joint_vel", "joint_acc", "settle_sec"):
        if _require(m, key, "motion") < 0:
            raise ConfigError(f"motion.{key} 는 음수일 수 없습니다")
    for key in ("travel_vel", "travel_acc", "fine_vel", "fine_acc"):
        _check_numbers(f"motion.{key}", _require(m, key, "motion"), 2)
    via = _require(m, "via_home", "motion")
    for task in ("insert", "eject"):
        if not isinstance(_require(via, task, "motion.via_home"), bool):
            raise ConfigError(f"motion.via_home.{task} 는 true/false 여야 합니다")

    p = cfg["payload"]
    for key in ("board_empty_kg", "board_printed_kg"):
        v = _require(p, key, "payload")
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0):
            raise ConfigError(f"payload.{key} 는 0 이상의 숫자 또는 null 이어야 합니다")
    _check_numbers("payload.cog", _require(p, "cog", "payload"), 3)

    g = cfg["gripper"]
    if _require(g, "backend", "gripper") not in GRIPPER_BACKENDS:
        raise ConfigError(f"gripper.backend 는 {GRIPPER_BACKENDS} 중 하나여야 합니다")
    if not 0 <= g.get("open_width", 0) <= 110:
        raise ConfigError("gripper.open_width 는 0~110mm (RG2 범위) 여야 합니다")
    if not 0 <= g.get("force", 0) <= 40:
        raise ConfigError("gripper.force 는 0~40N (RG2 범위) 여야 합니다")

    for kind in LOCATION_KINDS:
        locs = cfg[kind]
        if not isinstance(locs, dict) or not locs:
            raise ConfigError(f"{kind}: 위치가 최소 1개 필요합니다")
        for loc_id, loc in locs.items():
            _check_location(kind, loc_id, loc, ws)


# ---------------------------------------------------------------------------
def get_location(cfg, kind, loc_id):
    """작업에 쓸 위치를 반환. 없는 ID 이거나 좌표가 비어 있으면 LocationError."""
    locs = cfg[kind]
    if loc_id not in locs:
        raise LocationError(f"{KIND_LABEL[kind]}({kind} {loc_id}) 은 설정에 없는 ID 입니다. 사용 가능: {sorted(locs)}")
    loc = locs[loc_id]
    missing = [k for k in ("approach", "target") if loc.get(k) is None]
    if missing:
        raise LocationError(f"{KIND_LABEL[kind]}({kind} {loc_id}) 의 좌표 {missing} 가 아직 입력되지 않았습니다")
    return loc


def incomplete_ids(cfg):
    """좌표가 비어 있는 ID 목록 {kind: [id, ...]}."""
    return {
        kind: sorted(i for i, loc in cfg[kind].items() if loc.get("approach") is None or loc.get("target") is None)
        for kind in LOCATION_KINDS
    }
