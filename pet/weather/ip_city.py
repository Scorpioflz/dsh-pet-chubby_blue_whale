# -*- coding: utf-8 -*-
"""IP 定位城市：启动时根据 IP 地址检测城市，提醒设置默认城市。

优先使用高德 IP 定位 API（精度更高，需 API Key），回退到免费 API（ip-api.com / ipinfo.io）。
高德 API 文档：https://developer.amap.com/api/webservice/guide/api/ipconfig/
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request


_TIMEOUT = 5

_FREE_IP_APIS = [
    ("http://ip-api.com/json/?lang=zh", lambda d: d.get("city", "") if d.get("status") == "success" else ""),
    ("https://ipinfo.io/json", lambda d: d.get("city", "")),
]


def detect_city_by_amap(api_key: str) -> str | None:
    """通过高德 IP 定位 API 获取城市名。需高德 Web 服务 API Key。"""
    try:
        url = f"https://restapi.amap.com/v3/ip?key={urllib.parse.quote(api_key)}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") == "1":
            city = str(data.get("city", "")).strip()
            if city:
                return city
    except Exception:
        logging.exception("高德 IP 定位失败")
    return None


def detect_city_by_ip() -> str | None:
    """通过免费 IP 定位 API 获取城市名（多 API 容错）。失败返回 None。"""
    for url, extractor in _FREE_IP_APIS:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            city = str(extractor(data)).strip()
            if city:
                return city
        except Exception:
            continue
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


def ensure_weather_city(config=None, parent=None) -> None:
    """首次启动时如果城市列表为空，IP 定位 + 弹窗提醒设置默认城市。

    优先使用高德 API（精度更高），无 Key 时弹窗询问是否申请，拒绝则回退免费 API。
    """
    if config is None:
        config = _find_config()
    if config is None:
        return
    try:
        cities = config.get("weather_city_list", [])
        if cities:
            return
    except Exception:
        return

    city = None

    amap_key = ""
    try:
        amap_key = str(config.get("amap_api_key", "") or "")
    except Exception:
        pass

    if amap_key:
        city = detect_city_by_amap(amap_key)

    if not city:
        try:
            from PySide6.QtWidgets import QMessageBox, QInputDialog
            reply = QMessageBox.question(
                parent,
                "IP 定位服务",
                "免费 IP 定位精度较低（仅到省级出口）。\n是否使用高德 IP 定位服务？（精度更高，需自行申请 API Key）\n\n申请地址：https://lbs.amap.com/dev/key/app",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                key, ok = QInputDialog.getText(
                    parent, "高德 API Key", "请输入高德 Web 服务 API Key："
                )
                if ok and key.strip():
                    amap_key = key.strip()
                    config.set("amap_api_key", amap_key)
                    config.save()
                    city = detect_city_by_amap(amap_key)
        except Exception:
            logging.exception("高德 API Key 弹窗失败")

    if not city:
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