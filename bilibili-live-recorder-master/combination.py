import subprocess
import json
import re
import config
import importlib

def get_room_info(mid):
    command = [
        "curl",
        "-G",
        "https://api.live.bilibili.com/room/v1/Room/getRoomInfoOld",
        "--data-urlencode",
        f"mid={mid}"
    ]
    
    # 使用 utf-8 解碼
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    
    # 檢查命令是否成功
    if result.returncode == 0:
        try:
            # 將 JSON 字符串解析為字典
            data = json.loads(result.stdout)
            
            # 檢查返回代碼是否成功 (code == 0)
            if data.get("code") == 0:
                # 獲取所需字段
                live_status = data["data"].get("liveStatus")
                
                # 確認 liveStatus 是否為 1（如果需要）
                # if isinstance(live_status, int) and live_status == 1:
                room_status = data["data"].get("roomStatus")
                url = data["data"].get("url")
                title = data["data"].get("title")

                # 打印字段內容
                print("Room Status:", room_status)
                print("Live Status:", live_status)
                print("URL:", url)
                print("Title:", title)

                match = re.search(r'/(\d+)$', url)
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

    # 返回空字典或錯誤信息
    return {}

def write_updated_rooms_to_config():
    """將當前的 rooms 列表寫回到 config.py 文件中"""
    with open('config.py', 'r',encoding='utf-8') as file:
        lines = file.readlines()

    # 尋找並更新 rooms 變量的定義
    with open('config.py', 'w', encoding='utf-8') as file:
        for line in lines:
            if line.strip().startswith('rooms ='):
                # 將當前的 rooms 列表寫回文件
                 file.write(f"rooms = {config.rooms}  # 示例：['1075', '547028', '8694442']\n")
            else:
                file.write(line)


def read_mids_and_get_info_run(filename):
    with open(filename, 'r',encoding="utf-8") as file:
        for line in file:
            mid = line.strip()
            if mid.isdigit():  # 檢查 mid 是否為有效數字
                info = get_room_info(mid)
                if info:
                    config.add_room(info['Room ID'])
   
    print("Updated rooms list:", config.rooms)
    write_updated_rooms_to_config()
    subprocess.run(["python", "run.py"])

if __name__ == '__main__':
    read_mids_and_get_info_run("mid.txt")
