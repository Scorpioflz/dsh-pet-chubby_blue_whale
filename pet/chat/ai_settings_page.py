# -*- coding: utf-8 -*-
"""Modern settings AI 设置页 _AiSettingsPage。

从 modern_settings_dialog.py 纯机械搬移。现位于 pet/chat/ 下，原 `from .chat.xxx`
相对导入改为 `from .xxx`（级别变化）。
"""
from __future__ import annotations

import threading


from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..settings_widgets import (
    ModernSelect,
    _line_edit,
    BrowserSpinBox,
    BrowserDoubleSpinBox,
    ToggleSwitch,
    ResourcePathPicker,
    SettingsSection,
    SettingRow,
    SettingsCard,
)

from .themes import CHAT_UI_STYLE_LABELS, CHAT_UI_VIEW_ASPECT, theme_names
from .utils import _safe_emit


class _AiSettingsPage(QWidget):
    test_done = Signal(bool, str)


    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setObjectName("aiSettingsContent")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        from .models import ProviderConfig, SecretStore

        self.config = config
        self._provider_config_type = ProviderConfig
        self._secret_store_type = SecretStore
        self._test_connection = lambda c, timeout=10.0: (False, "已移除 OpenAI 兼容 provider 测试")
        self.settings = config.chat_settings()
        provider = self.settings.active_config
        self._test_thread = None
        self.test_done.connect(self._on_test_done)

        self.name = _line_edit(provider.name)
        self.url = _line_edit(provider.base_url)
        self.model = _line_edit(provider.model)
        self.key = _line_edit(password=True)
        self.prompt = QPlainTextEdit(self.settings.default_system_prompt)
        self.prompt.setMinimumSize(240, 80)
        self.timeout = BrowserSpinBox()
        self.timeout.setRange(1, 600)
        self.timeout.setSuffix(" 秒")
        self.timeout.setValue(int(provider.timeout))
        self.temperature = BrowserDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(provider.temperature)
        self.tokens = BrowserSpinBox()
        self.tokens.setRange(1, 131072)
        self.tokens.setValue(provider.max_tokens)
        self.skip_ssl = ToggleSwitch()
        self.skip_ssl.setChecked(not provider.verify_ssl)
        self.thinking_mode = ModernSelect(self, width=230)
        self.thinking_mode.addItem("跟随模型默认", "auto")
        self.thinking_mode.addItem("开启深度思考", "enabled")
        self.thinking_mode.addItem("关闭深度思考", "disabled")
        self.thinking_mode.setCurrentData(provider.thinking)
        self.reasoning_effort = ModernSelect(self, width=230)
        self.reasoning_effort.addItem("低（更快）", "low")
        self.reasoning_effort.addItem("高（默认）", "high")
        self.reasoning_effort.addItem("最大（最慢、最深入）", "max")
        self.reasoning_effort.setCurrentData(provider.reasoning_effort)
        self.chat_reply_voice = ToggleSwitch()
        self.chat_reply_voice.setChecked(bool(config.get("chat_reply_voice_enabled", False)))

        self.system_notify_check = ToggleSwitch()
        self._system_notify_dirty = False
        self.system_notify_check.setChecked(bool(config.get("system_notifications_enabled", True)))
        self.chat_ui_style = ModernSelect(self, width=190)
        for style_id, style_label in CHAT_UI_STYLE_LABELS.items():
            self.chat_ui_style.addItem(style_label, style_id)
        self.chat_ui_style.setCurrentData(str(config.get("chat_ui_style", "modern")))
        self.vision_same = ToggleSwitch()
        self.vision_same.setChecked(bool(provider.vision_same_as_chat))
        self.vision_model = _line_edit(provider.vision_model)
        self.vision_url = _line_edit(provider.vision_base_url)
        self.vision_key = _line_edit(password=True)

        self._background_themes = list(theme_names())
        self._background_values = {
            "classic": str(config.get("chat_background", "") or ""),
            "modern": str(config.get("modern_chat_background", "") or ""),
        }
        self._background_display = {
            "classic": {
                "opacity": int(config.get("chat_background_opacity", 100) or 100),
                "fill": str(config.get("chat_background_fill", "cover") or "cover"),
            },
            "modern": {
                "opacity": int(config.get("modern_chat_background_opacity", 100) or 100),
                "fill": str(config.get("modern_chat_background_fill", "cover") or "cover"),
            },
        }
        self._background_style = str(self.chat_ui_style.currentData() or "modern")
        self.background_select = ModernSelect(self, width=180)
        self.background_picker = ResourcePathPicker("", parent=self)
        self.background_opacity = BrowserSpinBox(self)
        self.background_opacity.setRange(10, 100)
        self.background_opacity.setSuffix(" %")
        self.message_card_opacity = BrowserSpinBox(self)
        self.message_card_opacity.setRange(10, 100)
        self.message_card_opacity.setSuffix(" %")
        self.message_card_opacity.setValue(
            int(config.get("modern_chat_card_opacity", 84) or 84)
        )
        self.background_fill = ModernSelect(self, width=160)
        self.background_fill.addItem("填充裁剪", "cover")
        self.background_fill.addItem("完整适应", "contain")
        self.background_fill.addItem("拉伸铺满", "stretch")
        self._bg_crop_edits: dict[str, list | None] = {}
        self._bg_edited_styles: set[str] = set()
        self._loading_background = False
        self.background_crop_btn = QPushButton("裁切取景…", self)
        self.background_crop_btn.clicked.connect(self._crop_background)
        self._populate_background_options(self._background_style)
        self.chat_ui_style.currentIndexChanged.connect(self._on_chat_ui_style_changed)
        self.background_select.currentIndexChanged.connect(self._on_background_edited)
        self.background_picker.edit.textChanged.connect(self._on_background_edited)
        self.background_picker.edit.textChanged.connect(self._update_background_visibility)
        self.background_opacity.valueChanged.connect(self._on_background_edited)
        self.background_fill.currentIndexChanged.connect(self._on_background_edited)
        self.background_fill.currentIndexChanged.connect(self._update_background_visibility)
        self.test_button = QPushButton("测试连接")
        self.test_button.clicked.connect(self._run_test)
        self.test_result = QLabel("验证当前 Provider、API 地址和凭据是否可用。")
        self.test_result.setWordWrap(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)
        root.addWidget(SettingsSection("模型与连接", [
            SettingRow("provider_name", "Provider 名称", "用于区分当前使用的模型服务。", self.name),
            SettingRow("api_url", "API 地址", "OpenAI Chat Completions 兼容服务地址。", self.url),
            SettingRow("model", "模型", "发送请求时使用的模型标识。", self.model),
            SettingRow("api_key", "API Key", "凭据优先保存到系统钥匙串。", self.key),
            SettingRow("system_prompt", "System Prompt", "定义桌宠对话时的身份、语气和行为。", self.prompt, stacked=True),
            SettingRow("connection_test", "连接测试", self.test_result.text(), self.test_button),
        ], self))
        thinking_rows = [
            SettingRow(
                "thinking_mode", "深度思考",
                "DeepSeek V4 等思考模型会先推理再回答，思考过程显示在回复上方（可折叠）。"
                "「跟随模型默认」不额外发送参数；开启后建议把「最大输出 Token」调到 8192 以上。",
                self.thinking_mode,
            ),
            SettingRow("reasoning_effort", "思考强度", "仅在「开启深度思考」时发送；强度越高越慢、越耗 Token。", self.reasoning_effort),
        ]
        root.addWidget(SettingsSection("深度思考", thinking_rows, self))
        self._reasoning_effort_row = thinking_rows[1]
        self.thinking_mode.currentIndexChanged.connect(self._update_thinking_visibility)
        self._update_thinking_visibility()
        root.addWidget(SettingsSection("系统通知", [
            SettingRow(
                "system_notifications_enabled", "系统通知",
                "对话完成 / 生成失败 / 需要授权时，即使切走窗口也会在桌面右下角提醒。",
                self.system_notify_check,
            ),
        ], self))
        root.addWidget(SettingsSection("助手回复朗读", [
            SettingRow(
                "chat_reply_voice_enabled", "念出回复",
                "AI 回复到达后按句念出来（含识图提问的回答）。与语音报时共用同一条"
                "音频通道，因此不会叠音；只念对话内容，不念歌词与代码。默认关闭。",
                self.chat_reply_voice,
            ),
        ], self))

        vision_rows = [
            SettingRow("vision_same", "视觉模型复用聊天模型", "开启后自动选择兼容的视觉模型，用于“看看屏幕”。", self.vision_same, parent=self),
            SettingRow("vision_model", "视觉模型", "关闭复用后使用的多模态模型标识；留空则自动推导。", self.vision_model, parent=self),
            SettingRow("vision_url", "视觉 API 地址", "留空复用聊天服务地址。", self.vision_url, parent=self),
            SettingRow("vision_key", "视觉 API Key", "留空复用聊天服务凭据。", self.vision_key, parent=self),
        ]
        root.addWidget(SettingsSection("视觉能力", vision_rows, self))
        self._vision_override_rows = vision_rows[1:]
        self.vision_same.toggled.connect(self._update_vision_visibility)
        self._update_vision_visibility(self.vision_same.isChecked())
        self.system_notify_check.toggled.connect(self._on_system_notify_edited)
        self._test_row = self.findChild(SettingRow, "settingRow_connection_test")
        if self._test_row is not None:
            self.test_result = self._test_row.hint_label
        root.addWidget(SettingsSection("生成参数（高级）", [
            SettingRow("timeout", "请求超时", "等待模型服务响应的最长时间。", self.timeout),
            SettingRow("temperature", "Temperature", "数值越高，回答越随机。", self.temperature),
            SettingRow("max_tokens", "最大输出 Token", "限制模型单次回复的最大长度；开启深度思考时思考过程也计入，建议 8192 以上。", self.tokens),
            SettingRow("skip_ssl", "跳过 SSL 证书验证", "仅用于本地网关或自签名证书。", self.skip_ssl),
        ], self, advanced=True))
        root.addStretch(1)

    def appearance_rows(self) -> list[SettingRow]:
        rows = [
            SettingRow(
                "chat_ui_style", "对话窗口",
                "肥鱼版 DeepSeek 提供宽屏现代体验；肥鱼牌小手机保留紧凑经典体验。",
                self.chat_ui_style, parent=self,
            ),
            SettingRow(
                "chat_background", "对话背景",
                "肥鱼版 DeepSeek 与肥鱼牌小手机均支持纯色、内置主题或自定义图片。",
                self.background_select, parent=self,
            ),
            SettingRow("chat_background_file", "自定义背景图片", "支持常见图片格式，使用绝对路径。", self.background_picker, parent=self),
            SettingRow("chat_background_opacity", "图片不透明度", "调节背景图可见强度；消息卡片会独立保证正文可读。", self.background_opacity, parent=self),
            SettingRow("chat_background_fill", "填充方式", "选择裁剪铺满、完整显示或拉伸铺满窗口；仅「填充裁剪」支持自定义取景。", self.background_fill, parent=self),
            SettingRow("chat_bg_crops", "裁切取景", "拖拽移动 + 滚轮缩放选区，决定背景取哪一块；不裁则按主题默认主体取景。", self.background_crop_btn, parent=self),
            SettingRow(
                "modern_chat_card_opacity", "消息卡片不透明度",
                "调节肥鱼版 DeepSeek 消息卡片透出背景的程度。",
                self.message_card_opacity, parent=self,
            ),
        ]
        self._background_file_row = rows[-5]
        self._background_detail_rows = rows[-4:-1]
        self._background_crop_row = self._background_detail_rows[-1]
        self._message_card_opacity_row = rows[-1]
        self.background_select.currentIndexChanged.connect(self._update_background_visibility)
        self._update_background_visibility()
        return rows

    def _current_background_value(self) -> str:
        value = self.background_select.currentData()
        return self.background_picker.text() if value == "custom" else str(value or "")

    def _capture_background_value(self) -> None:
        self._background_values[self._background_style] = self._current_background_value()
        self._background_display[self._background_style] = {
            "opacity": self.background_opacity.value(),
            "fill": str(self.background_fill.currentData() or "cover"),
        }

    def _populate_background_options(self, style: str) -> None:
        self._loading_background = True
        try:
            self.background_select.clear()
            self.background_select.addItem("纯色背景", "")
            for key, label in self._background_themes:
                self.background_select.addItem(label, f"builtin:{key}")
            self.background_select.addItem("自定义图片", "custom")
            value = str(self._background_values.get(style, "") or "")
            if value.startswith("builtin:") and self.background_select.findData(value) >= 0:
                self.background_select.setCurrentData(value)
                self.background_picker.setText("")
            elif value:
                self.background_select.setCurrentData("custom")
                self.background_picker.setText(value)
            else:
                self.background_select.setCurrentData("")
                self.background_picker.setText("")
            display = self._background_display.get(style, {})
            self.background_opacity.setValue(int(display.get("opacity", 100)))
            self.background_fill.setCurrentData(str(display.get("fill", "cover")))
        finally:
            self._loading_background = False
        self._update_background_visibility()

    def _on_background_edited(self, *_args) -> None:
        if not self._loading_background:
            self._bg_edited_styles.add(self._background_style)

    def _on_system_notify_edited(self, _checked: bool = False) -> None:
        self._system_notify_dirty = True

    def _on_chat_ui_style_changed(self, _index: int = -1) -> None:
        self._capture_background_value()
        self._background_style = str(self.chat_ui_style.currentData() or "modern")
        self._populate_background_options(self._background_style)

    def _update_thinking_visibility(self, *_args) -> None:
        self._reasoning_effort_row.setVisible(self.thinking_mode.currentData() == "enabled")
        card = self._reasoning_effort_row.parentWidget()
        if isinstance(card, SettingsCard):
            card.refresh_separators()

    def _update_vision_visibility(self, reuse_chat_model: bool) -> None:
        for row in self._vision_override_rows:
            row.setVisible(not reuse_chat_model)
        card = self._vision_override_rows[0].parentWidget() if self._vision_override_rows else None
        if isinstance(card, SettingsCard):
            card.refresh_separators()

    def _background_style_label(self) -> str:
        return CHAT_UI_STYLE_LABELS.get(self._background_style, self._background_style)

    def _background_fill_mode(self) -> str:
        return str(self.background_fill.currentData() or "cover")

    def _update_background_visibility(self, _index: int = -1) -> None:
        crop_row = getattr(self, "_background_crop_row", None)
        row = getattr(self, "_background_file_row", None)
        if row is not None:
            row.setVisible(self.background_select.currentData() == "custom")
            has_image = bool(self.background_select.currentData())
            for detail_row in getattr(self, "_background_detail_rows", []):
                detail_row.setVisible(has_image)
            if crop_row is not None:
                crop_row.setVisible(has_image and self._background_fill_mode() == "cover")
            card = row.parentWidget()
            if isinstance(card, SettingsCard):
                card.refresh_separators()
        card_opacity_row = getattr(self, "_message_card_opacity_row", None)
        if card_opacity_row is not None:
            card_opacity_row.setVisible(self._background_style == "modern")
        if crop_row is not None:
            title = f"裁切取景（{self._background_style_label()}）"
            if crop_row.label.text() != title:
                crop_row.label.setText(title)
                crop_row.control.setAccessibleName(title)
        if getattr(self, "background_crop_btn", None) is not None:
            self.background_crop_btn.setText("裁切取景…")
            self.background_crop_btn.setEnabled(True)

    def _crop_background(self) -> None:
        from .crop_dialog import CropDialog
        from .themes import get_theme
        from .widgets import resolve_bg_pixmap

        self.config.reload()
        value = self._current_background_value()
        pix = resolve_bg_pixmap(value) if value else None
        if pix is None:
            self.background_crop_btn.setText("无可裁背景")
            self.background_crop_btn.setEnabled(False)
            return
        _unset = object()
        initial = self._bg_crop_edits.get(value, _unset)
        if initial is _unset:
            initial = (self.config.get('chat_bg_crops', {}) or {}).get(value)
        if initial is None and value.startswith("builtin:"):
            theme = get_theme(value[8:])
            initial = tuple(theme["focus"]) if theme else None
        aspect = CHAT_UI_VIEW_ASPECT.get(self._background_style, CHAT_UI_VIEW_ASPECT["classic"])
        dlg = CropDialog(pix, initial, self, self._background_style_label(), aspect)
        accepted = dlg.exec()
        reset, box = dlg.result_box() if accepted else (False, None)
        dlg.deleteLater()
        if accepted:
            self._bg_crop_edits[value] = None if reset else [round(float(v), 4) for v in box]

    def provisional_config(self):
        provider = self.settings.active_config
        return self._provider_config_type(
            provider.provider_id,
            self.name.text().strip() or provider.name,
            self.url.text().strip(),
            provider.chat_path,
            self.model.text().strip(),
            provider.api_key_ref,
            self.key.text() or provider.api_key or self._secret_store_type().get(provider.api_key_ref),
            float(self.timeout.value()),
            float(self.temperature.value()),
            int(self.tokens.value()),
            verify_ssl=not self.skip_ssl.isChecked(),
            thinking=str(self.thinking_mode.currentData() or "auto"),
            reasoning_effort=str(self.reasoning_effort.currentData() or "high"),
        )

    def _run_test(self) -> None:
        if self._test_thread is not None and self._test_thread.is_alive():
            return
        self.test_button.setEnabled(False)
        self.test_button.setText("测试中…")
        self.test_result.setText("正在连接模型服务…")
        self._test_thread = threading.Thread(
            target=self._run_test_worker,
            args=(self.provisional_config(),),
            daemon=True,
            name="pet-modern-settings-connection-test",
        )
        self._test_thread.start()

    def _run_test_worker(self, provider) -> None:
        result = self._test_connection(provider, timeout=10.0)
        _safe_emit(self, "test_done", *result)

    def _on_test_done(self, ok: bool, message: str) -> None:
        self.test_button.setEnabled(True)
        self.test_button.setText("测试连接")
        self.test_result.setText(message)
        self.test_result.setStyleSheet("color: #16843b;" if ok else "color: #c9362b;")
        self._test_thread = None

    def save(self) -> None:
        self.config.reload()
        self.settings = self.config.chat_settings()
        p = self.settings.active_config
        p.name = self.name.text().strip() or p.name
        p.base_url = self.url.text().strip() or p.base_url
        p.model = self.model.text().strip() or p.model
        p.timeout = float(self.timeout.value())
        p.temperature = float(self.temperature.value())
        p.max_tokens = int(self.tokens.value())
        p.vision_model = self.vision_model.text().strip()
        p.vision_same_as_chat = self.vision_same.isChecked()
        p.vision_base_url = self.vision_url.text().strip()
        p.verify_ssl = not self.skip_ssl.isChecked()
        p.thinking = str(self.thinking_mode.currentData() or "auto")
        p.reasoning_effort = str(self.reasoning_effort.currentData() or "high")
        key = self.key.text()
        if key:
            if not self._secret_store_type().set(p.api_key_ref, key):
                p.api_key = key
        vkey = self.vision_key.text()
        if vkey:
            if not self._secret_store_type().set(p.vision_api_key_ref, vkey):
                p.vision_api_key = vkey
        self.settings.default_system_prompt = self.prompt.toPlainText().strip()
        self.config.set("chat_ui_style", self.chat_ui_style.currentData())
        self._capture_background_value()
        if "classic" in self._bg_edited_styles:
            self.config.set("chat_background", self._background_values["classic"])
            self.config.set("chat_background_opacity", self._background_display["classic"]["opacity"])
            self.config.set("chat_background_fill", self._background_display["classic"]["fill"])
        if "modern" in self._bg_edited_styles:
            self.config.set("modern_chat_background", self._background_values["modern"])
            self.config.set("modern_chat_background_opacity", self._background_display["modern"]["opacity"])
            self.config.set("modern_chat_background_fill", self._background_display["modern"]["fill"])
        if self._bg_crop_edits:
            crops = dict(self.config.get("chat_bg_crops", {}) or {})
            for key, box in self._bg_crop_edits.items():
                if box is None:
                    crops.pop(key, None)
                else:
                    crops[key] = box
            self.config.set("chat_bg_crops", crops)
            self._bg_crop_edits.clear()
        self.config.set("modern_chat_card_opacity", self.message_card_opacity.value())
        if self._system_notify_dirty:
            self.config.set("system_notifications_enabled", self.system_notify_check.isChecked())
        self.config.set("chat_reply_voice_enabled", self.chat_reply_voice.isChecked())
        self.config.set_chat_settings(self.settings)
