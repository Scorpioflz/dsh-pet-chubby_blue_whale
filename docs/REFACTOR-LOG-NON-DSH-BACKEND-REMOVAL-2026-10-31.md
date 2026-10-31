# PR 报告：非 DSH 后端移除（provider/persona/agent link）

> **基线**：`cc881933`（refactor: remove non-DSH provider, pet-side persona, non-DSH agent link）
> **续 commit**：UI 死代码清理 + 非 DSH Monitor 类定义移除（净 −2314 行）
> **分支**：`main`　**日期**：`2026-10-31`
> **范围**：25 文件修改 + 2 文件删除（净 −2997 行）
> **关联**：[`docs/task1-pet-memory-simplification.md`](../../docs/task1-pet-memory-simplification.md) §七、[`docs/DSH Reference Record.md`](../../docs/DSH Reference Record.md) §二.14

---

## 一、核心特性

桌宠只保留 DSH 作为唯一后端。移除：非 DSH provider 支持（OpenAI 兼容）、桌宠侧人设拼接（system prompt 首发 + 角色扮演引导 + 记忆引导）、联网搜索、非 DSH agent 联动（Claude/Cursor/OpenCode/CustomAgent monitor）。人设改由 DSH persona 插件（`dsh-persona-dafeiyu`，90⭐）通过 `systemPrompt.section()` 注入，可被 DeepSeek prompt caching 缓存。

| # | 能力 | 说明 |
|---|---|---|
| 1 | 非 DSH provider 移除 | `ProviderRouter` 删除，`ChatService` 直接用 `DshWebApiProvider`；`providers.py` 精简为 HTTP 工具模块 |
| 2 | 桌宠侧人设移除 | `PromptBuilder.build_messages()` 只返回用户消息；`default_system_prompt` 默认空串；`prompt_sync`/`system_sent` 逻辑移除 |
| 3 | 联网搜索移除 | `web_search.py` 删除（225 行）；`WebSearchSettings` 保留禁用桩（UI 兼容） |
| 4 | 非 DSH agent 联动移除 | `AgentLinkManager` 只创建 DSH monitor；卸载清理只保留 DSH bridge |

**红线 / 不变量**：DSH webapi 通信链路不变；`ChatService` 对外 API 不变；UI 不崩溃（断裂导入桩化）。

## 二、修改文件说明

### 实现

| 文件 | 增删 | 改动意图 |
|---|---|---|
| `pet/chat/providers.py` | +16 / −301 | 精简为 HTTP 工具模块：保留 `_make_ssl_context`/`build_browser_headers`/`normalize_chat_endpoint`（被 island/balance.py、screen_capture/translate.py 引用），re-export `ProviderError`/`StreamEvent`；移除 `OpenAICompatibleProvider`/`SSEParser`/`test_connection`/所有 web search 代码 |
| `pet/chat/web_search.py` | +0 / −225 | **删除**：联网搜索全量移除 |
| `pet/chat/prompt.py` | +32 / −123 | 移除 `ROLEPLAY_GUIDE`/`MEMORY_GUIDE`/`roleplay_context`/`time_context`/`stamp_message`；`build_messages()` 只返回 `[{'role':'user','content':user_text}]`；`effective_system_prompt` 返回空串 |
| `pet/chat/dsh_provider.py` | +4 / −47 | 移除 `ProviderRouter` 类；移除 `stream()` 中 `prompt_sync`/`system_sent` 逻辑；移除 session 创建和迁移中的 `system_sent` |
| `pet/chat/models.py` | +27 / −22 | `ProviderError`/`StreamEvent` 迁入；`WebSearchSettings`→禁用桩；`WEB_SEARCH_KEYED_ENGINES=()`/`WEB_SEARCH_ENGINES=()`；`ProviderConfig` 移除 `web_search`；`default_system_prompt`→空；`active_provider`→`dsh-webapi` |
| `pet/chat/service.py` | +3 / −3 | `ChatService.__init__` 直接用 `DshWebApiProvider`，不再经 `ProviderRouter` |
| `pet/chat/ai_settings_page.py` | +2 / −3 | 桩化断裂导入（`test_connection`/`WEB_SEARCH_KEYED_ENGINES`/`ENGINE_LABELS`） |
| `pet/chat/settings_dialog.py` | +5 / −1 | 桩化 `from .providers import test_connection` |
| `pet/config.py` | +4 / −33 | `_default_chat_data()` 只保留 `dsh-webapi` provider；移除 `openai-main`/`web_search` 默认值；`default_system_prompt`→空；`_merge_chat_data()` 移除 `openai-main` 引用；legacy 迁移 `openai-main`→`dsh-webapi` |
| `pet/agent_link/__init__.py` | +0 / −15 | `AgentLinkManager.__init__` 只创建 DSH monitor（移除 Claude/Cursor/OpenCode/CustomAgent monitor 实例化） |
| `pet/uninstall_cleanup.py` | +3 / −5 | 移除 Claude hooks 清理，只保留 DSH bridge 清理 |
| `pet/file_interpret/__init__.py` | +1 / −2 | 移除 `provider.web_search = None` 赋值 |

### 文档

| 文件 | 增删 | 改动意图 |
|---|---|---|
| `README.md` | +14 / −3 | Changelog 新增本次重构条目 |
| `README_ZH.md` | +13 / −3 | 同上中文版 |

### 未改动

- `pet/proactive/memory.py`、`pet/memory_trim.py` 未动（与 chat memory 无关）
- roleplay config keys (`roleplay_enabled`/`roleplay_scene`) 仍保留在 config.py 和 chat widgets 中（`build_messages` 忽略这些参数；纯死数据，不影响功能）

## 二·B、UI 死代码清理 + 非 DSH Monitor 类移除（续 commit）

| 文件 | 增删 | 改动意图 |
|---|---|---|
| `pet/chat/ai_settings_page.py` | +38 / −545 | 移除多 provider 管理 UI（combo/add/delete + 草稿逻辑）、web search 控件（5 个）、roleplay UI + `RoleplaySceneDialog` 类 |
| `pet/chat/settings_dialog.py` | +22 / −239 | 移除多 provider 管理 UI（combo/add/delete + 草稿逻辑 + `_apply_draft_to_provider`） |
| `pet/chat/models.py` | +3 / −18 | 移除 `WebSearchSettings` 类、`WEB_SEARCH_ENGINES`/`WEB_SEARCH_KEYED_ENGINES` 常量、`ChatSettings.web_search` 字段及 from_dict/to_dict 引用 |
| `pet/config.py` | +1 / −3 | 移除 `_redacted_data` 中 web_search api_key 剥离逻辑 |
| `pet/modern_settings_dialog.py` | +1 / −7 | 移除「场景扮演」section + web search 设置键；「深度思考与联网」→「深度思考」 |
| `pet/settings_default_marks.py` | +1 / −5 | 移除 web_search 默认值标记 |
| `pet/agent_link/__init__.py` | +4 / −440 | 移除 `ClaudeCodeMonitor`/`CursorMonitor`/`OpenCodeMonitor`/`CustomAgentMonitor` 类定义（387 行）；`AGENT_NAMES` 缩减为 `{"dsh":"DSH"}`；`_warn_if_agent_absent` 简化为 no-op；`set_enabled` 移除 claude 分支 |
| `tests/test_agent_link.py` | +0 / −527 | 移除 7 个测试类 + 2 个测试方法（引用已删除 Monitor 类） |
| `tests/test_chat_thinking_web_search.py` | +0 / −511 | **删除**：引用已删除的 `web_search.py` 模块 |
| `tests/test_agent_link_threads.py` | +1 / −35 | 移除 `CursorMonitor` import + `TestOpenCodeDbRotation` 类 |
| `tests/test_proactive.py` | +1 / −5 | 移除 `ClaudeCodeMonitor` import + monkeypatch + claude toggle |
| `tests/test_uninstall_cleanup.py` | +2 / −51 | 移除 `ClaudeCodeMonitor.uninstall_hooks` monkeypatch + claude_hooks 断言 + 2 个 claude 专属测试函数 |
| `tools/mem_probe.py` | +1 / −1 | 移除 `OpenCodeMonitor` 引用 |

## 三、实现要点

**providers.py 精简边界**：不能完全删除——`_make_ssl_context`、`build_browser_headers`、`normalize_chat_endpoint` 被 `pet/island/balance.py`（余额查询 HTTP）和 `pet/screen_capture/translate.py`（截图翻译 HTTP）引用。改为精简为 HTTP 工具模块，re-export `ProviderError`/`StreamEvent`（从 `models.py`）。

**UI 兼容桩策略（第一轮 cc881933，第二轮 c2e4d3ac 已全部移除）**：第一轮保留 `WebSearchSettings` 为禁用桩（UI 文件深嵌 web search 控件，直接移除会崩）。第二轮清理 UI 死代码后，`WebSearchSettings`/`WEB_SEARCH_*` 常量、roleplay 配置键（`roleplay_enabled`/`roleplay_scene`/`roleplay_cast`）、`RoleplaySceneDialog` 类、非 DSH Monitor 类（`ClaudeCodeMonitor`/`CursorMonitor`/`OpenCodeMonitor`/`CustomAgentMonitor`）全部移除。`ChatSettings` 保留 `providers` dict 和 `active_provider` 骨架（UI 大量引用），但默认只有 `dsh-webapi` 一个 provider。

**人设传递机制变更**：此前桌宠通过 `POST /sessions` 的 `systemPrompt` 字段首发人设，并通过 `prompt_sync` 在每轮对话时同步。现在 `default_system_prompt` 默认空串，`build_messages()` 只返回用户消息，`prompt_sync`/`system_sent` 逻辑移除。人设改由 DSH persona 插件通过 `ctx.systemPrompt.section()` 注入（固定 section 可被 prompt caching 缓存）。

## 四、性能分析

**方法（可复现）**：`python -c "import pet.app; import pet.chat.service; import pet.chat.dsh_provider; import pet.chat.providers; import pet.chat.prompt; import pet.chat.models; print('OK')"`　环境：`Windows 11 / Python 3.11`

| 指标 | 实测 | 归属 |
|---|---|---|
| 模块导入时间（全部子模块） | <1s（无报错） | 既有路径 |
| `build_messages()` 调用 | 返回单条 user 消息，无拼接 | 热路径——每轮对话 |
| `effective_system_prompt` | 返回空串（无字符串操作） | 热路径——session 创建 |
| `ChatService.__init__` provider 构造 | 直接 `DshWebApiProvider()`，无路由查表 | 启动路径 |

**结论**：① 稳态开销减少——`build_messages` 不再拼接 system prompt + memory_text + recall_text，每轮对话少 3 次字符串拼接；② `ProviderRouter` 移除后 provider 构造从查表+实例化变为直接实例化；③ 无新增系统调用/网络/磁盘/线程；④ 内存减少——`web_search.py` 225 行模块不再加载，`ProviderRouter` 类不再实例化。

## 五、实机运行记录

- **模块导入验证**：`python -c "import pet.app; ..."` 全部子模块导入通过，无 `ImportError`/`ModuleNotFoundError`。
- **聚焦测试**：chat/config/packaging 三域 299 测试通过（166+82+51），2 skipped。环境缺 `tzdata`/`numpy` 的 15 个测试文件未跑。
- **未做实机对话验证**：未启动桌宠确认 DSH webapi 对话链路正常、人设不再由桌宠首发。后续应启动桌宠 + DSH 确认。
- **`dsh-persona-dafeiyu` 插件已安装并配置好**：人设由 DSH persona 插件通过 `systemPrompt.section()` 注入。

## 六、测试与验证

| 门 | 命令 | 结果 |
|---|---|---|
| 模块导入 | `python -c "import pet.app; ..."` | ✅ 通过 |
| 静态检查 | `python -m ruff check pet tests scripts` | **未跑** |
| 聚焦 | `pytest tests/test_chat_*.py tests/test_config_*.py tests/test_packaging_*.py` | ✅ 299 passed, 2 skipped |
| 全量 | `python -m pytest -q` | **未跑**（15 文件因缺 tzdata/numpy 无法收集） |
| 架构红线 | `tests/test_architecture.py` | **未跑** |

## 七、已知限制与后续

1. **未跑全量测试**：15 文件因缺 `tzdata`/`numpy` 无法收集，应补装依赖后跑全量。
2. **未做实机对话验证**：应启动桌宠 + DSH 确认对话链路正常。

## 八、风险与回滚

- **影响面**：对话链路（provider 构造 + prompt 构建 + session 创建）、agent 联动（只 DSH）、卸载清理、UI 设置页（桩化导入）。
- **配置迁移**：`config.py` 的 `_merge_chat_data()` 自动将旧 `openai-main` provider 迁移为 `dsh-webapi`；`default_system_prompt` 旧值保留（不强制清空），但 `build_messages()` 不再使用它。
- **回滚**：`git revert c2e4d3ac cc881933` 即可恢复全部移除的代码。无残留状态或落盘数据问题（配置迁移是单向的，回滚后旧配置仍可用）。
- **主要风险**：若用户依赖非 DSH provider（如自建 OpenAI 兼容端点），本次改动后该功能不可用。但项目目标已明确只保留 DSH 作为唯一后端。
## 九、后续变动（2026-10-31 续）

### 9.1 roleplay 死代码 + 已删除功能测试/docs 清理（commit `6f74d57e`，净 −1033 行）

**源码**：`pet/config.py` 移除 `ROLEPLAY_*` 常量 + `_clean_roleplay_text` + roleplay 键默认值/归一化；`pet/chat/prompt.py` 移除 `build_messages` 的 roleplay 参数；`pet/chat/widgets.py`/`legacy_widgets.py`/`quick_chat.py` 移除 roleplay 参数传递；`pet/pet_profiles.py` 移除 roleplay 键。

**测试**：删除 `tests/test_chat_roleplay.py`（905 行）；`tests/test_config_schema.py`/`test_settings_default_marks.py`/`test_architecture.py` 更新。

**docs**：`AGENT_LINK_PROTOCOL.md` 更新 Monitor 引用；`DSH-BRIDGE-PET-EVENT-CONTRACT-2026-09-02.md` 移除 Custom Agent 段落。

### 9.2 `dsh-web-service` 插件安装检测（commit `27c21e2a`）

`dsh-web-service` 是桌宠的硬依赖（暴露 HTTP API）。新增 `pet/webapi_plugin_link.py` 检测模块；`pet/app.py` 添加 `_show_webapi_plugin_dialog()` + 启动检查；`pet/config.py` 添加 `webapi_plugin_remind` 键。83 测试通过，`is_installed()` 返回 `True`。

### 9.3 文档全面整理（本次 commit）

移除上游历史文档（191→13 条目）：119 个上游 PR-REPORT、8 个 RELEASE notes、7 个 plugin-phase 目录、plugin-roadmap 目录、35 个上游开发历史文档。保留：INDEX.md（重写）、AGENTS.md（精简 Context pointers）、DEV-HANDOVER.md、ONEDIR_PACKAGING.md、SETTINGS-CHANGE-GATES.md、STABLE_BUILDS.md、NETWORK-PROXY-AND-VPN、DSH-BRIDGE-PET-EVENT-CONTRACT、AGENT_LINK_PROTOCOL、PR-REPORT-NON-DSH-BACKEND-REMOVAL、PR-REPORT-TEMPLATE、agents/、third_party_doc/、screenshots/。README 添加指向 `dsh-selfuse-index` 索引仓库的链接。
## 十、Bug 修复（commit `fade273d` + `5f9c15bc`，2026-10-31）

重构后测试验证发现并修复 13 个 bug（3 个功能 bug + 10 个测试对齐）。

### 10.1 功能 bug（commit `fade273d`）

| Bug | 文件 | 问题 | 修复 |
|---|---|---|---|
| 1 | `pet/chat/legacy_widgets.py` | `new_session()` 缺 `invalidate_session` 调用（`b3a22be1` 漏修经典窗口路径） | 补加 invalidate 调用 |
| 7 | `pet/chat/settings_dialog.py` | keyring 不可用时 save 静默回退不弹警告 | 模块级导入 QMessageBox + 弹警告 |
| 12 | `pet/config.py` | `cc881933` 误删 `api_key_ref` 迁移逻辑：自定义 provider 继承的 `provider/openai-main` ref 不再迁移到自身，用户升级后凭据丢失 | 恢复迁移逻辑，覆盖 `openai-main` + `dsh-webapi` 两种 ref |

### 10.2 测试对齐（commit `5f9c15bc`）

| Bug | 文件 | 问题 | 修复 |
|---|---|---|---|
| 2 | `test_chat_subsystem.py` | 顶层导入已删的 `SSEParser`/`_is_cert_verify_error` → 143 测试无法收集 | 移除导入 |
| 3 | `test_chat_service.py` + `manual_ssl_proxy_check.py` | 引用已删的 `OpenAICompatibleProvider`/`SSEParser` | 删测试函数 + 删脚本 |
| 4 | `test_chat_subsystem.py` | `build_messages` 断言期望 system 消息（已改为只返回 user） | 更新断言 |
| 5 | `test_chat_subsystem.py` | config 迁移断言期望 `provider/openai-main`（已改为 `dsh-webapi`） | 更新断言 |
| 6 | `test_chat_subsystem.py` | spec 分组错误（`.spec` 用 `pet_entry.py` 带 chat，归错无 chat 列表） | 修正分组 |
| 8 | `test_chat_subsystem.py` | MessageBubble 断言期望 pin 按钮（已移除）+ 矛盾断言 | 删矛盾断言 + 重命名 |
| 9 | `test_chat_subsystem.py` | keyring 测试缺 `importorskip` → `ModuleNotFoundError` | 加 `importorskip` |
| 10 | `test_config_instance.py` | 3 处 `openai-main` → `dsh-webapi` | 更新 |
| 11 | `test_config_concurrent_save.py` | 5 处 `openai-main` → `dsh-webapi` | 更新 |
| 13 | `test_packaging_keyring_notices.py` | `test_windows_build_excludes_only_the_chat_subsystem` 期望 `build_onedir.ps1` 排除 `pet.chat`（no-chat 变体已改用独立 spec） | 删过时测试 |