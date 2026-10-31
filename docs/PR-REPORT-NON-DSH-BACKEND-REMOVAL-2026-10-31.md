# PR 报告：非 DSH 后端移除（provider/persona/agent link）

> **基线**：`cc881933`（refactor: remove non-DSH provider, pet-side persona, non-DSH agent link）
> **分支**：`main`　**日期**：`2026-10-31`
> **范围**：13 文件修改 + 1 文件删除（净 −683 行）
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

- `pet/agent_link/__init__.py` 中非 DSH Monitor **类定义**仍存在（6335 行文件，类未实例化但未删除——后续可清理死代码）
- UI 文件中多 provider 管理/联网搜索/人设编辑**控件**仍存在（已桩化导入不会崩，但控件是死代码——后续可清理）
- `pet/proactive/memory.py`、`pet/memory_trim.py` 未动（与 chat memory 无关）

## 三、实现要点

**providers.py 精简边界**：不能完全删除——`_make_ssl_context`、`build_browser_headers`、`normalize_chat_endpoint` 被 `pet/island/balance.py`（余额查询 HTTP）和 `pet/screen_capture/translate.py`（截图翻译 HTTP）引用。改为精简为 HTTP 工具模块，re-export `ProviderError`/`StreamEvent`（从 `models.py`）。

**UI 兼容桩策略**：`WebSearchSettings` 保留为禁用桩（UI 文件深嵌 web search 控件，直接移除会崩）。`WEB_SEARCH_KEYED_ENGINES = ()`、`WEB_SEARCH_ENGINES = ()` 保留为空元组。`ChatSettings` 保留 `providers` dict 和 `active_provider` 骨架（UI 大量引用），但默认只有 `dsh-webapi` 一个 provider。`ai_settings_page.py`/`settings_dialog.py` 中断裂导入桩化为本地 no-op 函数。

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
- **未跑全量 pytest 套件**：本次改动涉及 13 文件，应跑 `python -m pytest -q` 确认无回归，但**本次未跑**——如实登记。后续应补跑。
- **未做实机对话验证**：未启动桌宠确认 DSH webapi 对话链路正常、人设不再由桌宠首发。后续应启动桌宠 + DSH 确认。
- **未安装 `dsh-persona-dafeiyu` 插件**：人设移除后，若未安装 persona 插件，对话将无人设。后续应安装插件并导入人设文档。

## 六、测试与验证

| 门 | 命令 | 结果 |
|---|---|---|
| 模块导入 | `python -c "import pet.app; ..."` | ✅ 通过 |
| 静态检查 | `python -m ruff check pet tests scripts` | **未跑** |
| 聚焦 | — | **未跑** |
| 全量 | `python -m pytest -q` | **未跑** |
| 架构红线 | `tests/test_architecture.py` | **未跑** |

## 七、已知限制与后续

1. **未跑全量测试**：应补跑 `python -m ruff check pet tests scripts` + `python -m pytest -q`。
2. **UI 死代码未清理**：多 provider 管理/联网搜索/人设编辑控件仍存在（桩化不会崩，但控件是死代码）。
3. **`agent_link/__init__.py` 死代码**：非 DSH Monitor 类定义仍存在（6335 行文件，未实例化）。
4. **未安装 persona 插件**：应安装 `dsh-persona-dafeiyu` 并导入最终人设文档（`D:\华为云盘\DSH\大肥鱼_蓝鲸女仆人设_最终版.md`）。
5. **旧记忆数据迁移**：仍待做（见 task1 §三）。

## 八、风险与回滚

- **影响面**：对话链路（provider 构造 + prompt 构建 + session 创建）、agent 联动（只 DSH）、卸载清理、UI 设置页（桩化导入）。
- **配置迁移**：`config.py` 的 `_merge_chat_data()` 自动将旧 `openai-main` provider 迁移为 `dsh-webapi`；`default_system_prompt` 旧值保留（不强制清空），但 `build_messages()` 不再使用它。
- **回滚**：`git revert cc881933` 即可恢复全部移除的代码。无残留状态或落盘数据问题（配置迁移是单向的，回滚后旧配置仍可用）。
- **主要风险**：若用户依赖非 DSH provider（如自建 OpenAI 兼容端点），本次改动后该功能不可用。但项目目标已明确只保留 DSH 作为唯一后端。