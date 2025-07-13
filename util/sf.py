from typing import Union, Dict
from .fs import find_all
from .cmd import execute_cmd


def get_key_from_sn(key: str, sn: str, use_cache=False) -> Union[str, None]:
    config_file = find_all(f"{sn}.txt", use_cache=use_cache)
    if len(config_file) != 1:
        return None

    try:
        # We should get only one file
        config_file = config_file[0]
        config_data = parse_config_file(config_file)
        return config_data.get(key)
    except:
        return None


def parse_config_file(file: str) -> Dict[str, str]:
    result = {}
    with open(file, "r") as f:
        for line in f:
            if "=" in line:
                key, val = line.split("=", maxsplit=1)
                result[key] = val.strip()
    return result
