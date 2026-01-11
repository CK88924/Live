# combination.py
# -*- coding: utf-8 -*-

import subprocess
import json
import re
import config
import importlib


def _ensure_config():
    if not hasattr(config, "rooms"):
        config.rooms = []
    if not hasattr(config, "add_room"):
        def add_room(r):
            if r not in config.rooms:
                config.rooms.append(r)
        config.add_room = add_room


def get_room_id_from_mid(mid):
    url = "https://api.live.bilibili.com/room/v1/Room/getRoomInfoOld"
    cmd = ["curl", "-G", url, "--data-urlencode", f"mid={mid}"]

    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    try:
        data = json.loads(r.stdout)
        room_url = data.get("data", {}).get("url", "")
        m = re.search(r"/(\d+)$", room_url)
        return m.group(1) if m else None
    except Exception:
        return None


def write_rooms():
    with open("config.py", "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write(f"rooms = {config.rooms}\n")


def main():
    _ensure_config()

    with open("mid.txt", "r", encoding="utf-8") as f:
        for line in f:
            mid = line.strip()
            if mid.isdigit():
                rid = get_room_id_from_mid(mid)
                if rid:
                    config.add_room(rid)

    write_rooms()
    importlib.reload(config)
    subprocess.run(["python", "run.py"])


if __name__ == "__main__":
    main()
