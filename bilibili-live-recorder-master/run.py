# run.py
# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import requests
import multiprocessing
import urllib3
from Live import BiliBiliLive
import config
import utils
import subprocess

urllib3.disable_warnings()
proxies = {"http": None, "https": None}


class BiliBiliLiveRecorder(BiliBiliLive):
    def __init__(self, room_id, check_interval=5 * 60):
        super().__init__(room_id)
        self.inform = utils.inform
        self.print = utils.print_log
        self.check_interval = check_interval

    def check(self, interval):
        """檢測直播間狀態並獲取直播流 URL"""
        while True:
            try:
                room_info = self.get_room_info()
                if room_info.get('status'):
                    # 開播：通知 + 印出房名，然後取直播流 URL
                    self.inform(room_id=self.room_id, desp=room_info.get('roomname', ''))
                    self.print(self.room_id, room_info.get('roomname', ''))
                    urls = self.get_live_urls()
                    if not urls:
                        self.print(self.room_id, '未取得直播流 URL，稍後重試')
                        time.sleep(interval)
                        continue
                    return urls
                else:
                    self.print(self.room_id, '等待開播')
            except Exception as e:
                self.print(self.room_id, f'Error while checking status: {e}')
            time.sleep(interval)

    def record(self, record_url, output_filename, max_retries=3):
        """錄制直播並寫入文件，支持超時重試和動態更新 URL"""
        retries = 0
        while retries < max_retries:
            try:
                headers = {
                    'Accept-Encoding': 'identity',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
                    'Referer': re.findall(r'(https://.*\/).*\.flv', record_url)[0]
                }
                self.print(self.room_id, f'√ 正在錄制... {self.room_id}')
                resp = self.session.get(record_url, stream=True, headers=headers, timeout=30)
                with open(output_filename, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                break  # 成功完成錄制
            except requests.exceptions.Timeout:
                retries += 1
                self.print(self.room_id, f"超時，正在嘗試更新流 URL（第 {retries} 次）")
                try:
                    new_urls = self.get_live_urls()
                    if not new_urls:
                        self.print(self.room_id, "未取得新 URL，稍後再試")
                        time.sleep(3)
                        continue
                    record_url = new_urls[0]
                except Exception as e:
                    self.print(self.room_id, f"更新流 URL 失敗: {e}")
                    time.sleep(3)
            except Exception as e:
                self.print(self.room_id, f"Error while recording: {e}")
                break
        else:
            self.print(self.room_id, f"多次重試失敗，錄制終止: {output_filename}")

    def fix_metadata(self, filename):
        """使用 ffmpeg 修覆視頻元數據"""
        try:
            fixed_filename = filename.replace('.flv', '_fixed.flv')
            cmd = ['ffmpeg', '-i', filename, '-c', 'copy', fixed_filename]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.print(self.room_id, f'修覆完成: {fixed_filename}')
        except Exception as e:
            self.print(self.room_id, f'Error while fixing metadata: {e}')

    def run(self):
        """主流程：檢測直播狀態 -> 錄制 -> 修覆元數據"""
        while True:
            try:
                urls = self.check(interval=self.check_interval)
                filename = utils.generate_filename(self.room_id)
                utils.checkRecordDirExisted()
                output_file = os.path.join(os.getcwd(), 'files', filename)
                self.record(urls[0], output_file)
                self.print(self.room_id, f'錄制完成: {output_file}')
                self.fix_metadata(output_file)  # 修覆元數據
            except Exception as e:
                self.print(self.room_id, f'Error while checking or recording: {e}')


if __name__ == '__main__':
    # 保底：確保 config 有 rooms
    if not hasattr(config, 'rooms'):
        config.rooms = []

    # 取得輸入房號或從配置文件加載
    if len(sys.argv) == 2:
        input_ids = [str(sys.argv[1]).strip()]
    elif len(sys.argv) == 1:
        input_ids = list(config.rooms)  # 從配置加載
    else:
        raise ValueError('請檢查輸入命令是否正確，例如：python run.py 10086')

    # 若清單為空，給出提示並停止（避免啟無進程）
    if not input_ids:
        print('[提示] 沒有指定房間號，且 config.rooms 為空。')
        print('  → 可用法一：python run.py 10086')
        print('  → 可用法二：先用 combination.py 產生 rooms 再自動啟動')
        sys.exit(0)

    # 多進程錄制
    tasks = [multiprocessing.Process(target=BiliBiliLiveRecorder(room_id).run) for room_id in input_ids]
    for task in tasks:
        task.start()
    for task in tasks:
        task.join()
