# -*- coding: utf-8 -*-
"""IP 定位城市：启动时根据 IP 地址检测城市，提醒设置默认城市。

首次启动且城市列表为空时，通过 IP 定位获取城市名，弹窗提醒用户设置。
"""

from __future__ import annotations

import json
import logging
import urllib.request


_IP_API_URL = "http://ip-api.com/json/?lang=zh"
_TIMEOUT = 5


def detect_city_by_ip() -> str | None:
    """通过 IP 定位获取9定位获取城市名。失败返回 None。"""
    try:
        req = urllib.request.Request(_IP_API_URL)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") == "success":
            city = str(data.get("city", "")).strip()
            if city:
                return city
    except Exception:
        logging.exception("IP 定位失败")
    return None


def _find_config():
    """从 QApplication 顶层窗口中找到 config 对象。"""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            return None
        for w in app.topLevelWidgets():
            cfg = getattr(w, "config", None) or getattr(w, "cfg", None)
            if cfg is not None and callable(getattr(cfg, "get", None)) and callable(getattr(cfg, "save", None)):
                return cfg
    except Exception:
        pass
    return None


def ensure_weather_city(parent=None) -> None:
    """首次启动时如果城市列表为空，IP 定位 + 弹窗提醒设置默认城市。

    在 GUI 线程调用（ChatService.__init__ 中）。
    """
    config = _find_config()
    if config is None:
        return
    try:
        cities = config.get("weather_city_list", [])
        if cities:
            return
    except Exception:
        return
    city = detect_city_by_ip()
    if not city:
        return
    try:
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            parent,
            "天气城市",
            f"检测到你在「{city}」，是否设为默认天气城市？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            config.set("weather_city", city)
            config.set("weather_city_list", [city])
            config.save()
            logging.info("IP 定位城市已设置: %s", city)
    except Exception:
        logging.exception("天气城市弹窗失败")