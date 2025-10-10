# utils.py
# -*- coding: utf-8 -*-
import time
import requests
import config
import os

# 允許沒有 send_key；僅在 send_key 存在且啟用時才組 URL
SEND_KEY = getattr(config, 'send_key', '') or ''
ENABLE_INFORM = bool(getattr(config, 'enable_inform', False))
INFORM_URL = f'https://sctapi.ftqq.com/{SEND_KEY}.send' if (SEND_KEY and ENABLE_INFORM) else None


def get_current_time(time_format):
    """取得目前時間字串"""
    current_struct_time = time.localtime(time.time())
    current_time = time.strftime(time_format, current_struct_time)
    return current_time


def generate_filename(room_id):
    """產生檔名：日期_時間_房號.flv"""
    data = dict()
    data['c_time'] = get_current_time('%Y%m%d_%H%M')
    data['room_id'] = room_id
    return '_'.join(data.values()) + '.flv'


def inform(room_id, desp=''):
    """Server酱通知；沒有 send_key 或未啟用則略過"""
    if INFORM_URL:
        try:
            param = {
                'title': f'直播间：{room_id} 开始直播啦！',
                'desp': desp,
            }
            resp = requests.get(url=INFORM_URL, params=param,
                                verify=False, proxies={"http": None, "https": None}, timeout=10)
            if resp.status_code == 200:
                print_log(room_id=room_id, content='通知完成！')
        except Exception:
            pass  # 出錯不影響錄製


def print_log(room_id='None', content='None'):
    """統一日誌格式"""
    brackets = '[{}]'
    time_part = brackets.format(get_current_time('%Y-%m-%d %H:%M:%S'))
    room_part = brackets.format('直播间: ' + room_id)
    print(time_part, room_part, content)


def checkRecordDirExisted():
    """確保 ./files 目錄存在"""
    dirs = os.path.join(os.getcwd(), 'files')
    if not os.path.exists(dirs):
        os.mkdir(dirs)


if __name__ == '__main__':
    print(generate_filename('1075'))
    print_log(content='开始录制')
