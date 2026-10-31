# dsh-pet-chubby_blue_whale

> **继承声明**｜基于 [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT License, Copyright (c) 2026 Merzlin）个人自用再开发。保留原版权声明（[`LICENSE`](LICENSE)）与第三方声明（[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)）。

**DSH (DeepSeek Harness) 的桌宠前端**，通过 dsh-web-service 插件的会话 API 接入 DSH。

> **项目目标**：将桌宠的核心能力（记忆、人设、对话等）逐步迁移到 DSH 插件中——**做减法，不做加法**。桌宠自身逐渐回退为一个薄前端：只负责动画、输入和展示。所有智能（记忆、人设、推理）都住在 DSH 插件里，跨会话、跨工作区共享。

[English](README.md)

## 功能

- **对话**：通过 DSH Web Service 会话 API（`/sessions/:id/prompt-stream`）实现连续对话，DSH 侧显示为同一会话
- **角色对应工作区**：每个桌宠角色绑定独立 DSH 工作区（`~/.dsh-pet-workspace/<char_id>`），工作区内共享记忆
- **记忆**：由 DSH 插件 `@dsh-pet/memory`（基于 fish-memory 改造，14 天半衰期）按工作区共享记忆，桌宠前端只做纯 UI；记忆开关按角色配置，默认开启
- **看看屏幕/截图提问**：截图上传到 DSH 会话（`POST /sessions/:id/files`）→ 提问 → 气泡显示回复
- **余额查询**：通过 dsh-balance-panel 插件查询 DeepSeek 余额
- **IP 定位城市**：首次启动检测城市，提醒设置默认天气城市
- **自动自言自语**：每天通过 DSH API 以桌宠身份自动生成自言自语候选词（含热搜、新闻、吐槽），替换更新不累计
- **不发布、无 CI/CD、无 Release**，仅供自行封装使用
- 依赖管理用 uv + `pyproject.toml`（Python 3.14+）
- 上游同步：`git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git && git fetch upstream`

> **平台验证**：当前修改版**仅在 Windows 11 上验证通过**。Linux/macOS 尚未验证。

## DSH 插件依赖

| 插件 | 用途 | 地址 | 安装 |
|---|---|---|---|
| `dsh-web-service` | REST API 服务（会话/工作区/文件上传/SSE 流式对话） | [toddpan/dsh-webapi](https://github.com/toddpan/dsh-webapi) | `dsh plugin --profile web add @toddpan/dsh-webapi` |
| `@dsh-pet/memory` | 按工作区共享的长期记忆（基于 fish-memory 改造，14 天半衰期） | 内置 `integrations/dsh-pet-memory/` | 启动时自动检测并弹窗提示安装 |
| `@wycto/dsh-balance-panel` | 余额查询 REST 端点 `GET /dsh-balance-panel` | [wycto/dsh-balance-panel](https://github.com/wycto/dsh-balance-panel) | `dsh plugin --profile web add @wycto/dsh-balance-panel` |

> **注意**：`@dsh-pet/memory` 与原版 `dsh-fish-memory` 都注册 `remember` 工具，**不可装在同一个 DSH profile**。安装前如已有 fish-memory，先卸载：`dsh plugin --profile <profile> remove dsh-fish-memory`。

## 建议安装的插件（未内置）

| 插件 | 用途 | 地址 |
|---|---|---|
| `dsh-persona-dafeiyu` | 人设库：内置角色，支持导入自定义人设，按工作区分档生效，热切换无需重启。通过 `ctx.systemPrompt.section()` 注入（prompt caching 友好） | [huaizhuanghub/dsh-persona-dafeiyu](https://github.com/huaizhuanghub/dsh-persona-dafeiyu) |

## 插件引用与致谢

### 自行改造的插件

| 插件 | 基于 | 改动 | 源地址 |
|---|---|---|---|
| `@dsh-pet/memory` | [Yuuyuko-uu/dsh-fish-memory](https://github.com/Yuuyuko-uu/dsh-fish-memory) | 按工作区共享记忆；`<system-reminder>` 检索过滤；queryGate 小库保护（0.8→0.5，<10 条跳过）；设置页会话→工作区；打包目录编码修复 | [Yuuyuko-uu/dsh-fish-memory](https://github.com/Yuuyuko-uu/dsh-fish-memory) |

### 依赖的插件（未改动）

| 插件 | 用途 | 源地址 |
|---|---|---|
| `dsh-web-service` | REST/SSE API 服务 | [toddpan/dsh-webapi](https://github.com/toddpan/dsh-webapi) |
| `@wycto/dsh-balance-panel` | DeepSeek 余额查询 | [wycto/dsh-balance-panel](https://github.com/wycto/dsh-balance-panel) |

### 建议安装的插件（未安装）

| 插件 | 用途 | 源地址 |
|---|---|---|
| `dsh-persona-dafeiyu` | 人设/system prompt 管理（按工作区，热切换） | [huaizhuanghub/dsh-persona-dafeiyu](https://github.com/huaizhuanghub/dsh-persona-dafeiyu) |
| `dsh-whale-musume-persona` | 鲸鱼娘（大肥鱼）人设 | [Kaalia0912/dsh-whale-musume-persona](https://github.com/Kaalia0912/dsh-whale-musume-persona) |
| `dsh-prompt-persona` | 从设置页编辑 deployment persona | [Xilin3/dsh-prompt-persona](https://github.com/Xilin3/dsh-prompt-persona) |

---

## 目录

- [从源码运行](#从源码运行)
- [打包](#打包)
- [素材包说明](#素材包说明)
- [数据目录](#数据目录)
- [修改记录](#修改记录)
- [许可证与致谢](#许可证与致谢)

---

## 从源码运行

需要 Python 3.14+。使用 uv 管理依赖与虚拟环境：

```powershell
uv sync                    # 按 pyproject.toml 安装依赖到 .venv
uv run python -m pet       # 启动桌宠
```

## 打包

### 安装包（exe）

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1
```

产物：`dist-onedir\dsh-pet-chubby_blue_whale-setup.exe`（~500MB，含全部素材，免管理员权限）

### 增量更新（exe，不含素材）

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_update.ps1
```

产物：`dist-onedir\dsh-pet-chubby_blue_whale-update-setup.exe`（~100MB，不含动画素材，保留已有素材）

### 便携版（zip）

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_portable.ps1
```

产物：`dist-onedir\dsh-pet-chubby_blue_whale-portable.zip`（~500MB，解压即用）

| 脚本 | 素材 | ISCC | portable.zip | 大小 |
|---|---|---|---|---|
| `build_installer.ps1` | ✅ | ✅ | ❌ | ~500MB |
| `build_update.ps1` | ❌ | ✅ | ❌ | ~100MB |
| `build_portable.ps1` | ✅ | ❌ | ✅ | ~500MB |

**前提**：[uv](https://docs.astral.sh/uv/) 已安装；安装包/增量更新需 Inno Setup 7（默认 `D:\Tool\Inno Setup 7\ISCC.exe`）。

## 素材包说明

仓库自带 **106 个 WebM 动画**（`assets/characters/shenshen/videos/`）。打包时通过 `convert_frameseq_progress.py` 生成帧序列（WebP）。

`packs-index.json` 中的素材包（core + extra1-6，~1.45GB）是打包好的帧序列，与 106 个 WebM 一一对应。

| 目录 | 来源 | 格式 | 使用场景 |
|---|---|---|---|
| `videos/` | 仓库自带 | WebM | 源素材（开发调试） |
| `anim/` | 素材包安装 | WebP 帧序列 | 安装包用户 |
| `frameseq/` | 运行时生成 | WebP 帧序列 | 有仓库的用户 |

运行时优先用 `anim/`（如果有），否则从 `videos/` 自动生成 `frameseq/`。

## 数据目录

| 系统 | 数据目录 |
|---|---|
| Windows | `%APPDATA%/dsh-pet-chubby_blue_whale/` |
| macOS | `~/Library/Application Support/dsh-pet-chubby_blue_whale/` |
| Linux | `~/.config/dsh-pet-chubby_blue_whale/` |

```text
config.json                # 全局设置
config-slot-0.json         # 主宠的每宠设置
dsh_session.json           # 角色工作区/会话映射
dsh_workspaces.json        # 角色工作区绑定 + 记忆开关
sessions/<character_id>/   # 会话历史
pet.log
```

## 修改记录

> **合并策略**：`git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git && git fetch upstream && git merge upstream/main`

### 新增文件

| 文件 | 用途 |
|---|---|
| `pet/dsh_api.py` | DSH Web Service REST API 客户端 |
| `pet/chat/dsh_provider.py` | `DshWebApiProvider`（DSH 会话 API 流式对话） |
| `pet/dsh_workspace.py` | 按角色绑定工作区 + 记忆开关 |
| `pet/memory_plugin_link.py` | 记忆插件安装检查与一键安装 |
| `integrations/dsh-pet-memory/` | DSH 记忆插件（基于 fish-memory 改造） |
| `pet/dsh_self_talk.py` | 每天自动生成自言自语候选词 |
| `pet/weather/ip_city.py` | IP 定位城市 |
| `tools/convert_frameseq_progress.py` | 帧序列转换器 |
| `scripts/build_installer.ps1` | 完整安装包打包脚本 |
| `scripts/build_update.ps1` | 增量更新打包脚本 |
| `scripts/build_portable.ps1` | 便携版打包脚本 |
| `packaging/dsh-pet-chubby_blue_whale.iss` | Inno Setup 脚本 |

### 修改文件

| 文件 | 改动 |
|---|---|
| `pet/chat/service.py` | 直接注入 `DshWebApiProvider`（无 `ProviderRouter`）；移除记忆提炼 hook |
| `pet/chat/prompt.py` | 移除人设/扮演/记忆引导；`build_messages` 只返回用户消息（DSH 管历史与人设） |
| `pet/chat/providers.py` | 精简为 HTTP 工具（`_make_ssl_context`、`build_browser_headers`、`normalize_chat_endpoint`）；移除 `OpenAICompatibleProvider`、`SSEParser`、`test_connection`、联网搜索 |
| `pet/chat/models.py` | `ProviderError`/`StreamEvent` 迁入；`WebSearchSettings`→禁用桩；`default_system_prompt` 默认→空；`active_provider` 默认→`dsh-webapi`；`ProviderConfig` 移除 `web_search` |
| `pet/chat/dsh_provider.py` | 移除 `ProviderRouter`；移除 `prompt_sync`/`system_sent`（DSH persona 插件处理人设） |
| `pet/chat/ai_settings_page.py` | 桩化 `test_connection`/`web_search` 导入（UI 清理待续） |
| `pet/chat/settings_dialog.py` | 桩化 `test_connection` 导入 |
| `pet/config.py` | 只保留 `dsh-webapi` provider；移除 `openai-main`；移除 `web_search` 默认值；`default_system_prompt`→空 |
| `pet/file_interpret/__init__.py` | 移除 `provider.web_search` 赋值 |
| `pet/agent_link/__init__.py` | `AgentLinkManager` 只创建 DSH monitor；移除 Claude/Cursor/OpenCode/CustomAgent |
| `pet/uninstall_cleanup.py` | 移除 Claude hooks 清理；只保留 DSH bridge 清理 |
| `pet/chat/ai_settings_page.py` | 新增 DSH 记忆插件设置区 |
| `pet/chat/widgets.py` / `pet/legacy_widgets.py` | 移除记忆相关 UI 与逻辑 |
| `pet/config.py` | 默认 provider 改为 `dsh-webapi`；清理废置记忆键 |
| `pet/vision.py` | 截图提问 DSH 分支 |
| `pet/window.py` | 看看屏幕 DSH 分支 |
| `pet/overlay_shell.py` | 看看屏幕 overlay DSH 分支；合并自言自语候选词 |
| `pet/app.py` | 启动检查：工作区绑定、记忆插件、城市检测、自言自语 |
| `pet/window_alerts.py` | `merge_dsh_texts`：从独立文件读取自言自语 |
| `pet/pack_download.py` | 素材包 URL 顺序（代理优先） |
| `scripts/build_onedir.ps1` | 统一名称；加 `-SkipAssets` |
| `pyproject.toml` | Python 3.14 + uv |
| `.gitignore` | 加 CodeArts、uv、tmp/ |
| `integrations/dsh-pet-memory/lib/index.js` | ① `<system-reminder>` 过滤 ② queryGate 0.8→0.5 + 小库保护 ③ 工作区去重 ④ 编码修复 |
| `integrations/dsh-pet-memory/lib/client.js` | 设置页"会话"→"工作区" |
| `README.md` | 英文翻译 + 插件引用 |
| `THIRD_PARTY_NOTICES.md` | 删除 Android，新增自用组件 |

### 删除文件

| 文件/目录 | 原因 |
|---|---|
| `.github/` | 不需要 CI/CD |
| `android/` | 不需要 Android |
| `pet/chat/memory.py` | 桌宠自带记忆（1104 行），已下沉到插件 |
| `pet/chat/memory_recall.py` | 记忆回捞（531 行） |
| `pet/chat/memory_extract.py` | 记忆提炼（306 行） |
| `pet/chat/web_search.py` | 联网搜索（225 行）→ 已移除；DSH 侧处理联网搜索 |

### 配置说明

```json
{
  "chat": {
    "active_provider": "dsh-webapi",
    "providers": {
      "dsh-webapi": {
        "base_url": "http://127.0.0.1:3080/api/v1",
        "api_key": "<DSH API Key>"
      }
    }
  }
}
```

## 许可证与致谢

**MIT License**（见 [`LICENSE`](LICENSE)）。第三方素材见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

- [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT, Copyright (c) 2026 Merzlin）— 上游项目
- [PC2005-cloud/dsh-pet](https://github.com/PC2005-cloud/dsh-pet) — 动画素材基础
- [MeteorNOX/DeepSeek-Balance-Whale-Widget](https://github.com/MeteorNOX/DeepSeek-Balance-Whale-Widget) — 余额气泡参考
- [Yuuyuko-uu/dsh-fish-memory](https://github.com/Yuuyuko-uu/dsh-fish-memory) — `@dsh-pet/memory` 记忆插件基础
- [huaizhuanghub/dsh-persona-dafeiyu](https://github.com/huaizhuanghub/dsh-persona-dafeiyu) — 建议安装的人设插件