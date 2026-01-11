# Live/BilibiliLive.py
# -*- coding: utf-8 -*-

from .BaseLive import BaseLive
import time
import os


class BiliBiliLive(BaseLive):
    def __init__(self, room_id):
        super().__init__()
        self.room_id = str(room_id)
        self.site_name = "BiliBili"
        self.site_domain = "live.bilibili.com"

        # DEBUG 開關（預設關）
        self.debug_api = os.getenv("BILI_DEBUG_API", "0") == "1"

    # ==================================================
    # 直播狀態（防禦式）
    # ==================================================
    def get_room_status(self):
        def _get():
            url = "https://api.live.bilibili.com/room/v1/Room/get_info"
            resp = self.common_request(
                "GET",
                url,
                {"room_id": self.room_id}
            ).json()

            # code != 0（含 -412 風控）
            if resp.get("code") != 0:
                return False, ""

            data = resp.get("data") or {}
            self.room_id = str(data.get("room_id", self.room_id))

            return data.get("live_status") == 1, data.get("title", "")

        try:
            return self.retry(_get, retry=3, base_delay=5)
        except Exception:
            return False, ""

    # ==================================================
    # 新版 play_info（2026 穩定）
    # ==================================================
    def get_play_info_v2(self):
        url = "https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo"
        params = {
            "room_id": self.room_id,
            "protocol": "0,1",
            "format": "0,1",
            "codec": "0,1",
            "qn": 10000,
            "platform": "web",
            "ptype": 8,
        }

        resp = self.common_request("GET", url, params).json()

        if resp.get("code") != 0:
            msg = resp.get("message") or resp.get("msg") or "unknown error"
            raise RuntimeError(f"play_info api error: code={resp.get('code')} msg={msg}")

        data = resp.get("data")
        if not data:
            msg = resp.get("message") or resp.get("msg") or "no message"
            summary = f"play_info missing data; code={resp.get('code')} msg={msg}"

            if self.debug_api:
                print(f"[DEBUG][play_info] room={self.room_id} response={resp}")

            raise RuntimeError(summary)

        playurl = data.get("playurl_info", {}).get("playurl", {})
        urls = []

        for stream in playurl.get("stream", []):
            protocol_name = stream.get("protocol_name") # http_stream, http_hls
            for fmt in stream.get("format", []):
                format_name = fmt.get("format_name") # flv, ts
                for codec in fmt.get("codec", []):
                    base = codec.get("base_url")
                    for ui in codec.get("url_info", []):
                        urls.append({
                            "url": ui["host"] + base + ui["extra"],
                            "protocol": protocol_name,
                            "format": format_name
                        })

        if not urls:
            raise RuntimeError("play_info returned no playable urls")

        return urls

    # ==================================================
    # 指數退避（避免 API 連打）
    # ==================================================
    def retry(self, func, retry=5, base_delay=2):
        delay = base_delay
        for _ in range(retry):
            try:
                return func()
            except Exception:
                time.sleep(delay)
                delay *= 2
        raise RuntimeError("retry failed")
