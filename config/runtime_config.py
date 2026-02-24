import json
from dataclasses import dataclass

from config.channel_config import DEFAULT_CHANNEL_MAP
from config.target_config import DEFAULT_MULTIPLIER


@dataclass
class RuntimeConfig:
    base_target: float | None
    channel_map: dict
    multiplier_map: dict


def load_runtime_config(config_file) -> RuntimeConfig:
    """Load optional JSON config uploaded from Streamlit file_uploader."""
    if config_file is None:
        return RuntimeConfig(
            base_target=None,
            channel_map=DEFAULT_CHANNEL_MAP.copy(),
            multiplier_map=DEFAULT_MULTIPLIER.copy(),
        )

    payload = json.load(config_file)
    if not isinstance(payload, dict):
        raise ValueError("runtime config must be a JSON object")

    base_target = payload.get("base_target")
    if base_target is not None:
        base_target = float(base_target)

    channel_map = DEFAULT_CHANNEL_MAP.copy()
    user_channel_map = payload.get("channel_map", {})
    if not isinstance(user_channel_map, dict):
        raise ValueError("channel_map must be an object")
    channel_map.update({str(k): str(v) for k, v in user_channel_map.items()})

    multiplier_map = DEFAULT_MULTIPLIER.copy()
    user_multiplier_map = payload.get("multiplier_map", {})
    if not isinstance(user_multiplier_map, dict):
        raise ValueError("multiplier_map must be an object")
    multiplier_map.update({str(k): float(v) for k, v in user_multiplier_map.items()})

    return RuntimeConfig(
        base_target=base_target,
        channel_map=channel_map,
        multiplier_map=multiplier_map,
    )
