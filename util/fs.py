import os
from typing import List
from .consts import CONFIG_PATH, WIN_PATH

config_cache = {}


def find_all(name: str, path: str = WIN_PATH, use_cache: bool = False) -> List[str]:
    result = []
    if use_cache and config_cache.get(path):
        for file in config_cache[path]:
            if name in file:
                result.append(file)
    else:
        if not config_cache.get(path):
            config_cache[path] = set()

        for root, dirs, files in os.walk(path):
            if CONFIG_PATH in root:
                joined_path = os.path.join(root, name)
                if name in files:
                    result.append(joined_path)
                for filename in files:
                    config_cache[path].add(os.path.join(root, filename))

    return result
