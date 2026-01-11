# run.py
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import multiprocessing
from multiprocessing import Semaphore

from Live import BiliBiliLive
import config
import utils

# =========================
# CPU 控制
# =========================
CPU_LIMIT = max(1, multiprocessing.cpu_count() // 2)
record_semaphore = Semaphore(CPU_LIMIT)


class BiliBiliLiveRecorder(BiliBiliLive):
    def __init__(self, room_id, check_interval=60):
        super().__init__(room_id)
        self.print = utils.print_log
        self.inform = utils.inform
        self.check_interval = check_interval

    # =========================
    # ffmpeg 錄影
    # =========================
    def record_with_ffmpeg(self, stream_url, filename, is_flv=False):
        headers = (
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36\r\n"
            "Referer: https://live.bilibili.com/\r\n"
        )
        cmd = [
            "ffmpeg",
            "-loglevel", "warning",
            "-stats",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-rw_timeout", "20000000",
            "-headers", headers,
            "-i", stream_url,
            "-c", "copy",
        ]
        
        # HLS might need some extra bitstream filtering for AAC, 
        # but for FLV 'copy' is usually sufficient.
        if not is_flv:
            cmd.extend(["-bsf:a", "aac_adtstoasc"])
            
        cmd.append(filename)
        subprocess.run(cmd, check=False)

    # =========================
    # 主流程
    # =========================
    def run(self):
        while True:
            try:
                live, title = self.get_room_status()
                if not live:
                    self.print(self.room_id, "等待開播")
                    time.sleep(self.check_interval)
                    continue

                self.inform(room_id=self.room_id, desp=title)
                self.print(self.room_id, f"🎬 開播：{title}")

                urls = self.retry(self.get_play_info_v2)

                # 優先順序：FLV > HLS (如果 PREFER_FLV 為 True)
                prefer_flv = getattr(config, "PREFER_FLV", True)
                
                selected_stream = None
                if prefer_flv:
                    selected_stream = next((u for u in urls if u["format"] == "flv"), None)
                
                if not selected_stream:
                    selected_stream = next((u for u in urls if u["format"] == "ts" or "m3u8" in u["url"]), None)

                if not selected_stream:
                    raise RuntimeError("no playable stream found")

                stream_url = selected_stream["url"]
                is_flv = selected_stream["format"] == "flv"

                utils.checkRecordDirExisted()
                
                # 根據格式決定副檔名
                ext = ".flv" if is_flv else ".mp4"
                filename = utils.generate_filename(self.room_id)
                # Ensure we use the correct extension
                if filename.endswith(".flv") and not is_flv:
                    filename = filename.replace(".flv", ".mp4")
                elif filename.endswith(".mp4") and is_flv:
                    filename = filename.replace(".mp4", ".flv")
                elif not filename.endswith(ext):
                    filename += ext

                output = os.path.join(os.getcwd(), "files", filename)

                with record_semaphore:
                    self.print(self.room_id, f"🎥 取得 CPU slot，開始錄影 ({selected_stream['format']})")
                    self.record_with_ffmpeg(stream_url, output, is_flv=is_flv)

                self.print(self.room_id, f"✔ 錄影完成：{output}")

            except Exception as e:
                self.print(self.room_id, f"錯誤：{e}")
                time.sleep(10)


if __name__ == "__main__":
    if not hasattr(config, "rooms"):
        config.rooms = []

    rooms = [sys.argv[1]] if len(sys.argv) == 2 else list(config.rooms)

    if not rooms:
        print("沒有房間號")
        sys.exit(0)

    jobs = [
        multiprocessing.Process(
            target=BiliBiliLiveRecorder(room_id).run
        )
        for room_id in rooms
    ]

    for j in jobs:
        j.start()
    for j in jobs:
        j.join()
