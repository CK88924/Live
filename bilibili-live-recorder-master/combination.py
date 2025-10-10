# combination.py
# -*- coding: utf-8 -*-
import subprocess
import json
import re
import config
import importlib
import os

def _ensure_config_basics():
    """確保 config 至少有 rooms 和 add_room"""
    if not hasattr(config, 'rooms'):
        config.rooms = []
    if not hasattr(config, 'add_room'):
        def _add_room(room_id):
            room_id = '' if room_id is None else str(room_id).strip()
            if room_id and room_id not in config.rooms:
                config.rooms.append(room_id)
        config.add_room = _add_room

def get_room_info(mid):
    """根據 mid 呼叫 API 拿到房間資訊"""
    command = [
        "curl", "-G",
        "https://api.live.bilibili.com/room/v1/Room/getRoomInfoOld",
        "--data-urlencode", f"mid={mid}"
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")

    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            if data.get("code") == 0:
                live_status = data["data"].get("liveStatus")
                room_status = data["data"].get("roomStatus")
                url = data["data"].get("url")
                title = data["data"].get("title")

                print("Room Status:", room_status)
                print("Live Status:", live_status)
                print("URL:", url)
                print("Title:", title)

                match = re.search(r'/(\d+)$', url or '')
                if match:
                    room_id = match.group(1)
                    print("Room ID:", room_id)
                    return {
                        "Room Status": room_status,
                        "Live Status": live_status,
                        "URL": url,
                        "Title": title,
                        "Room ID": room_id
                    }
            else:
                print("API Error:", data.get("message"))
        except json.JSONDecodeError:
            print("Failed to parse JSON.")
    else:
        print("Error:", result.stderr)
    return {}

def _write_rooms_line(lines, rooms_list):
    """更新或補上 rooms = [...]"""
    wrote = False
    out = []
    for line in lines:
        if not wrote and line.strip().startswith('rooms ='):
            out.append(f"rooms = {rooms_list}  # 示例：['1075', '547028', '8694442']\n")
            wrote = True
        else:
            out.append(line)
    if not wrote:
        out.append(f"\n# 由 combination.py 自動補上\nrooms = {rooms_list}  # 示例：['1075', '547028', '8694442']\n")
    return out

def write_updated_rooms_to_config():
    """把目前的 rooms 清單寫回 config.py"""
    path = 'config.py'
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write("# -*- coding: utf-8 -*-\nrooms = []\n")
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    new_lines = _write_rooms_line(lines, config.rooms)
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def read_mids_and_get_info_run(filename):
    """讀取 mid.txt → 取房間 → 更新 config.rooms → 啟動 run.py"""
    _ensure_config_basics()
    with open(filename, 'r', encoding="utf-8") as file:
        for line in file:
            mid = line.strip()
            if mid.isdigit():
                info = get_room_info(mid)
                if info and info.get('Room ID'):
                    config.add_room(info['Room ID'])

    print("Updated rooms list:", config.rooms)
    write_updated_rooms_to_config()
    importlib.reload(config)
    subprocess.run(["python", "run.py"])

if __name__ == '__main__':
    read_mids_and_get_info_run("mid.txt")
