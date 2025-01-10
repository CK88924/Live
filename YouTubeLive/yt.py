import os
import time
import subprocess
import requests
import multiprocessing
from multiprocessing import Manager
from dotenv import load_dotenv

# 檢查直播狀態
def check_live_status(api_key, channel_id, currently_recording, live_streams, retries=3, delay=5):
    """檢查頻道是否正在直播，並保存直播信息到列表
    """
    attempt = 0
    while attempt < retries:
        attempt += 1
        print(f"Checking channel ID {channel_id}, Attempt {attempt} of {retries}")
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&type=video&eventType=live&key={api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if 'items' in data and len(data['items']) > 0:
                for item in data['items']:
                    video_id = item['id']['videoId']
                    live_url = f"https://www.youtube.com/watch?v={video_id}"
                    channel_name = item['snippet']['channelTitle']
                    print(f"Detected live stream: {channel_name}, URL: {live_url}")

                    # 如果該頻道未在錄製中，保存到直播列表
                    if not currently_recording.get(channel_name, False) and (live_url, channel_name) not in live_streams:
                        live_streams.append((live_url, channel_name))
                    else:
                        print(f"{channel_name} is already recording or live stream already listed. Skipping...")
                return True
            else:
                print(f"Channel ID {channel_id} is not live.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data for channel ID {channel_id}: {e}")

        if attempt < retries:
            print(f"Retrying after {delay} seconds...")
            time.sleep(delay)

    print(f"Finished all retries for channel ID {channel_id}. No live stream detected.")
    return False

# 模擬錄製命令
def run_ytarchive(live_url, channel_name, currently_recording):
    """執行 ytarchive 命令進行錄製
    """
    command = [
        "ytarchive",
        live_url,
        "best"
    ]
    try:
        print(f"開始錄製：{channel_name}，URL：{live_url}")
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if result.returncode == 0:
            print(f"錄製完成：{channel_name}")
            print(result.stdout)
        else:
            print(f"錄製失敗：{channel_name}")
            print(result.stderr)
    except Exception as e:
        print(f"錄製出錯：{channel_name}，錯誤：{e}")
    finally:
        # 標誌該頻道的錄製已完成
        print(f"錄製完成：{channel_name}")
        currently_recording[channel_name] = False

# 主監控函數
def run_monitoring(channel_id_list, api_key):
    """定期檢查頻道是否正在直播
    """
    with Manager() as manager:
        currently_recording = manager.dict()
        
        while True:
            live_streams = manager.list()  # 用於保存所有檢測到的直播
            processes = []
            
            for channel_id in channel_id_list:
                print(f"開始檢查頻道：{channel_id}")
                
                # 每個頻道的檢查作為一個進程
                process = multiprocessing.Process(target=check_live_status, args=(api_key, channel_id, currently_recording, live_streams))
                processes.append(process)
                process.start()

            # 等待所有檢查進程完成
            for process in processes:
                process.join()

            # 檢查完成後統一處理錄製
            for live_url, channel_name in live_streams:
                currently_recording[channel_name] = True
                process = multiprocessing.Process(target=run_ytarchive, args=(live_url, channel_name, currently_recording))
                process.start()

            print("Waiting 30 minutes before the next round of checks...")
            time.sleep(30 * 60)  # 每 30 分鐘執行一次檢查

# 從文件讀取頻道 ID
def read_channels(filename):
    """從文件讀取頻道 ID
    """
    channel_id_list = []
    try:
        with open(filename, 'r',encoding="utf-8") as file:
            for line in file:
                channel_id = line.strip()
                if channel_id:
                    channel_id_list.append(channel_id)
        print(f"Loaded channel IDs: {channel_id_list}")
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
    return channel_id_list

# 主函數
if __name__ == '__main__':
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    channel_id_list = read_channels("channel_id.txt")
    if channel_id_list:
        run_monitoring(channel_id_list, API_KEY)
    else:
        print("No channels found. Exiting...")
