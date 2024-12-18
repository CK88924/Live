# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 22:18:11 2024

@author: user
"""
import sys
import subprocess
import concurrent.futures

def read_urls(filename):
    """讀取頻道名稱列表"""
    channel_urls_list = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            print(f"正在打開文件：{filename}")
            for line in file:
                url = line.strip()  # 移除行尾的空白字符
                if url:  # 確保不是空行
                    print(f"讀取到的頻道連結: {url}")
                    channel_urls_list.append(url)
        print("頻道連結列表:", channel_urls_list)
    except FileNotFoundError:
        print(f"錯誤: 文件 {filename} 找不到。返回空列表。")
    except Exception as e:
        print(f"讀取文件時發生錯誤：{e}")
    return channel_urls_list

def download_stream(twitch_url):
    """執行 twitch-dlp 的下載功能"""
    command = ['path\to\npm\\twitch-dlp.cmd', twitch_url, '--retry-streams', '60', '--live-from-start']
    try:
        subprocess.run(command, check=True)
        print(f'{twitch_url} 下載完成')
    except subprocess.CalledProcessError as e:
        print(f'{twitch_url} 下載失敗，錯誤訊息：{e}')
    except Exception as e:
        print(f'執行指令時發生錯誤：{e}')

if __name__ == '__main__':
    print(sys.executable)
    # 指定存放頻道連結的文件名稱
    filename = "urls.txt"

    # 讀取頻道連結
    twitch_channels = read_urls(filename)

    # 使用 ThreadPoolExecutor 同時監聽多個頻道
    if twitch_channels:  # 確保有頻道連結可供處理
        print(f"開始監聽 {len(twitch_channels)} 個頻道...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(download_stream, twitch_channels)
    else:
        print("沒有可監聽的頻道連結。請檢查文件內容。")
