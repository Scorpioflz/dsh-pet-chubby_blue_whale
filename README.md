# dsh-pet-chubby_blue_whale

> **继承声明**｜基于 [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT License, Copyright (c) 2026 Merzlin）个人自用再开发。保留原版权声明（[`LICENSE`](LICENSE)）与第三方声明（[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)）。

## 自用定位

本项目是 **DSH (DeepSeek Harness) 的桌宠前端**，通过 dsh-web-service 插件的会话 API 接入 DSH：

- **对话**：通过 DSH Web Service 会话 API（`/sessions/:id/prompt-stream`）实现连续对话，DSH 侧显示为同一会话
- **角色对应工作区**：每个桌宠角色绑定独立 DSH 工作区（`~/.dsh-pet-workspace/<char_id>`），工作区内共享记忆
- **记忆**：由 DSH 插件 `@dsh-pet/memory`（基于 fish-memory 改造）按工作区共享记忆，桌宠前端只做纯 UI；记忆开关按角色配置，默认开启
- **看看屏幕/截图提问**：截图上传到 DSH 会话（`POST /sessions/:id/files`）→ 提问 → 气泡显示回复
- **余额查询**：通过 dsh-balance-panel 插件查询 DeepSeek 余额
- **IP 定位城市**：首次启动检测城市，提醒设置默认天气城市
- **自动自言自语**：每天通过 DSH API 以桌宠身份自动生成自言自语候选词（含热搜、新闻、吐槽），替换更新不累计
- **不发布、无 CI/CD、无 Release**，仅供自行封装使用
- 依赖管理用 uv + `pyproject.toml`（Python 3.14+）
- 上游同步：`git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git && git fetch upstream`

> **平台验证**：当前修改版**仅在 Windows 11 上验证通过**。Linux/macOS 由于没有使用条件，尚未进行验证。

## DSH 插件依赖

本桌宠依赖以下 DSH 插件：

| 插件 | 用途 | 地址 | 安装 |
|---|---|---|---|
| `dsh-web-service` | REST API 服务（会话/工作区/文件上传/SSE 流式对话） | [toddpan/dsh-webapi](https://github.com/toddpan/dsh-webapi) | `dsh plugin --profile web add @toddpan/dsh-webapi` |
| `@dsh-pet/memory` | 按工作区共享的长期记忆（基于 fish-memory 改造，14 天半衰期） | 内置 `integrations/dsh-pet-memory/` | 设置 → AI → API 列表选 `dsh-webapi` → DSH 记忆插件 → 一键安装 |
| `@wycto/dsh-balance-panel` | 余额查询 REST 端点 `GET /dsh-balance-panel` | [wycto/dsh-balance-panel](https://github.com/wycto/dsh-balance-panel) | `dsh plugin --profile web add @wycto/dsh-balance-panel` |

## 目录

- [从源码运行](#从源码运行)
- [打包](#打包)
- [素材包说明](#素材包说明)
- [数据目录](#数据目录)
- [修改记录](#修改记录)
- [项目来源与素材声明](#项目来源与素材声明)
- [许可证与致谢](#许可证与致谢)

---

## 从源码运行

需要 Python 3.14+。使用 uv 管理依赖与虚拟环境：

```powershell
uv sync                    # 按 pyproject.toml 安装依赖到 .venv
uv run python -m pet       # 启动桌宠
```

依赖管理通过 `pyproject.toml`（uv 方式），无需手动 pip install。

## 打包

### 安装包（exe）

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1
```

产物：`dist-onedir\dsh-pet-chubby_blue_whale-setup.exe`（双击安装，免管理员权限，含全部素材 ~500MB）

### 增量更新（exe，不含素材）

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_update.ps1
```

产物：`dist-onedir\dsh-pet-chubby_blue_whale-update-setup.exe`（~100MB，不含动画素材，安装时不覆盖已有素材）

适用于日常代码更新：打包时跳过素材（`-SkipAssets`），安装时只替换代码和依赖，保留已有的动画素材。首次安装需用完整安装包。

### 便携版（zip）

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_portable.ps1
```

产物：`dist-onedir\dsh-pet-chubby_blue_whale-portable.zip`（解压即用，含全部素材）

三个脚本共享前置步骤（uv sync → PyInstaller），区别：

| 脚本 | 素材 | ISCC | portable.zip | 产物大小 |
|---|---|---|---|---|
| `build_installer.ps1` | ✅ 含 | ✅ | ❌ 跳过 | ~500MB |
| `build_update.ps1` | ❌ 不含 | ✅ | ❌ 跳过 | ~100MB |
| `build_portable.ps1` | ✅ 含 | ❌ | ✅ 生成 | ~500MB |

**前提**：
- [uv](https://docs.astral.sh/uv/) 已安装
- 安装包/增量更新需 Inno Setup 7（ISCC 路径在脚本中配置，默认 `D:\Tool\Inno Setup 7\ISCC.exe`）

## 素材包说明

### 仓库素材 vs 素材包

仓库中自带 **106 个 WebM 动画**（`assets/characters/shenshen/videos/`），分布在 click/drag/events/idle/move/random/turn 目录。打包时通过 `convert_frameseq_progress.py` 从 WebM 生成帧序列（WebP），无需额外下载。

`packs-index.json` 中的素材包（core + extra1-6，共 ~1.45GB）是**打包好的帧序列**（WebP 逐帧），与仓库中 106 个 WebM 一一对应，不多不少。素材包是给**安装包用户**用的（没有仓库、不想自己转换的用户）。

### anim/ vs frameseq/ 目录

| 目录 | 来源 | 格式 | 使用场景 |
|---|---|---|---|
| `videos/` | 仓库自带 | WebM 视频 | 源素材（开发调试） |
| `anim/` | 素材包安装 | WebP 帧序列 | 安装包用户（无源视频，帧序列随包下发） |
| `frameseq/` | `convert_frameseq.py` 生成 | WebP 帧序列 | 有仓库的用户（从 WebM 转换） |

运行时 `library.py` 根据是否有素材包索引决定用哪套：
- **有素材包**（`anim/` 存在）→ 直接用 `anim/` 中的帧序列，不需要 `frameseq/`
- **无素材包** → 从 `videos/` 中的 WebM 自动生成 `frameseq/`（运行时首跑自动供给）

两者**可以共存**，不互相替换。优先用素材包（如果有）。

### 手动导入素材包

设置 → **角色与素材** → 点击 **"从本地文件安装…"** → 选择下载的 zip 文件。

### 帧序列转换

打包时自动执行 `convert_frameseq_progress.py` 生成帧序列（带进度和 ETA），已有则跳过。被 Ctrl+C 打断后下次运行会跳过已完成的 clip，幂等安全。

## 数据目录

设置与 DSH 会话保存在数据目录里（重装不会丢失）：

| 系统 | 数据目录 |
|---|---|
| Windows | `%APPDATA%/dsh-pet-chubby_blue_whale/` |
| macOS | `~/Library/Application Support/dsh-pet-chubby_blue_whale/` |
| Linux | `~/.config/dsh-pet-chubby_blue_whale/` |

目录中主要包含：

```text
config.json                # 全局设置
config-slot-0.json         # 主宠的每宠设置
dsh_session.json           # 角色工作区/会话映射（每角色一个 DSH 工作区）
dsh_workspaces.json        # 角色工作区绑定 + 记忆开关
sessions/<character_id>/   # 会话历史
pet.log
```

## 修改记录

> 本节记录所有对原作者代码的修改，便于后续合并上游更新。
>
> **合并策略**：`git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git && git fetch upstream && git merge upstream/main`。冲突时以本节为参考保留自用改动。

### 新增文件

| 文件 | 用途 |
|---|---|
| `pet/dsh_api.py` | DSH Web Service REST API 客户端（工作区/会话/上传/SSE 流式） |
| `pet/chat/dsh_provider.py` | `DshWebApiProvider`（每角色一个工作区 + 会话 API 连续对话 + 附件上传 + 记忆 toggle）+ `ProviderRouter` |
| `pet/dsh_workspace.py` | 按角色绑定工作区 + 记忆开关配置（`dsh_workspaces.json`） |
| `pet/memory_plugin_link.py` | 记忆插件 `@dsh-pet/memory` 安装检查与一键安装 |
| `integrations/dsh-pet-memory/` | DSH 记忆插件（基于 fish-memory 改造，按工作区共享记忆，14 天半衰期） |
| `pet/dsh_self_talk.py` | 每天通过 DSH API 以桌宠身份自动生成自言自语候选词（含热搜、新闻、吐槽），独立文件存储 |
| `pet/weather/ip_city.py` | IP 定位城市：优先高德 API（精度高，需 Key），回退免费 API |
| `tools/convert_frameseq_progress.py` | 帧序列转换器（带进度显示和 ETA） |
| `scripts/build_installer.ps1` | 完整安装包打包脚本（PyInstaller + ISCC，含素材） |
| `scripts/build_update.ps1` | 增量更新打包脚本（PyInstaller + ISCC，不含素材，`-SkipAssets`） |
| `scripts/build_portable.ps1` | 便携版打包脚本（PyInstaller + zip，含素材） |
| `scripts/run_all_tests.ps1` | 逐个运行所有测试（带超时） |
| `packaging/dsh-pet-chubby_blue_whale.iss` | Inno Setup 安装包脚本 |

### 修改文件

| 文件 | 改动 |
|---|---|
| `pet/chat/service.py` | 注入 `ProviderRouter`（按 provider_id 路由到 DSH 或原 OpenAI）；移除记忆提炼 hook |
| `pet/chat/prompt.py` | 新增 `MEMORY_GUIDE` 引导段，`build_messages` 追加记忆使用引导 |
| `pet/chat/ai_settings_page.py` | 新增 DSH 记忆插件设置区 + 一键安装按钮 |
| `pet/chat/widgets.py` / `pet/legacy_widgets.py` | 移除记忆相关 UI 与逻辑 |
| `pet/quick_chat.py` / `pet/modern_settings_dialog.py` | 移除记忆相关引用 |
| `pet/config.py` | 默认 provider 改为 `dsh-webapi`；`APP_DIR_NAME` 改为 `dsh-pet-chubby_blue_whale`（无变体后缀）；`reload()` 键列表加 `dsh_self_talk_enabled`；清理废置记忆键（`chat_memory_enabled` 等 3 个） |
| `pet/vision.py` | 截图提问 DSH 分支：上传截图到 DSH 会话 → 提问 → 返回回复 |
| `pet/window.py` | 看看屏幕 DSH 分支：截图 → 上传到 DSH 会话 → 提问 → 气泡 |
| `pet/overlay_shell.py` | 看看屏幕 DSH 分支（overlay 版）；`PetSprite` + `ScreenHost` 的 `_show_random_self_talk` 合并 DSH 候选词 |
| `pet/app.py` | 启动时检查角色工作区绑定 + 记忆插件安装提醒 + 天气城市 + 自言自语生成（`QTimer.singleShot`）；余额查询 DSH 分支（`show_balance` + `_quiet_balance_refresh` + `_balance_worker_dsh`） |
| `pet/settings_features.py` | 天气功能激活时触发城市检测 |
| `pet/window_alerts.py` | `merge_dsh_texts` 函数：从独立文件 `dsh_self_talk_texts.json` 读取 DSH 候选词并合并；`show_random_self_talk` 调用合并 |
| `pet/pack_download.py` | 素材包下载 URL 顺序反转（代理优先，GitHub 官方最后） |
| `scripts/build_onedir.ps1` | 去掉变体相关，统一为 `dsh-pet-chubby_blue_whale`；加 `-SkipAssets` 开关 |
| `pyproject.toml` | Python 3.14 + uv 依赖管理（`[project]` dependencies + `[project.optional-dependencies]` build） |
| `.gitignore` | CodeArts + uv 配置不追踪 |
| `README.md` | 继承声明 + 自用定位 + 精简 |
| `THIRD_PARTY_NOTICES.md` | 删除 Android 声明，新增自用版第三方组件 |
| 2 个测试文件 | 删除引用已删目录的测试函数 |
| 多个测试文件 | 适配默认 provider 改动 + Python 3.14 pathlib 兼容性 |

### 删除文件

| 文件/目录 | 原因 |
|---|---|
| `.github/` | 不需要 CI/CD |
| `android/` | 不需要 Android 客户端 |
| `update.json` | 更新功能不需要 |
| `requirements.txt` | 依赖整合到 pyproject.toml |
| `注意事项.txt` | 内容整合到 README |
| 4 个 android 脚本 | android 相关 |
| 3 个 android/CI 测试 | 引用已删目录 |
| `pet/chat/memory.py` | 桌宠自带记忆存储（1104 行），已下沉到 `@dsh-pet/memory` 插件 |
| `pet/chat/memory_recall.py` | 记忆回捞（531 行） |
| `pet/chat/memory_extract.py` | 记忆提炼（306 行） |
| `tests/test_chat_memory*.py` | chat memory 测试 |
| `tests/test_memory_recall.py` | memory_recall 测试 |

### 配置说明

DSH Web API provider 配置（`config.json`）：

```json
{
  "chat": {
    "active_provider": "dsh-webapi",
    "providers": {
      "dsh-webapi": {
        "name": "DSH Web API",
        "base_url": "http://127.0.0.1:3080/api/v1",
        "chat_path": "/chat/completions",
        "api_key": "<DSH API Key>",
        "model": ""
      }
    }
  }
}
```

切换回原 AI API 对话：把 `active_provider` 改为 `"openai-main"`。

### 合并上游更新步骤

```bash
git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git
git fetch upstream
git merge upstream/main
# 处理冲突时参考上方"修改文件"部分，保留自用改动
git push origin main
```

## 项目来源与素材声明

**上游代码**来自原作者 [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT License, Copyright (c) 2026 Merzlin）。桌宠的基础功能（窗口、动画、菜单、设置等）完整来自上游，详见 [上游 README](https://github.com/MerZlin/dsh-pet-indesktop#readme)。

第三方素材与组件授权声明见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## 许可证与致谢

本项目采用 **MIT License**（见仓库根目录 `LICENSE`），第三方素材与组件授权声明见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

**原作者：**

- [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT License, Copyright (c) 2026 Merzlin）：本项目基于此开源项目个人自用再开发。
- [PC2005-cloud/dsh-pet](https://github.com/PC2005-cloud/dsh-pet)：原作者参考的动画素材基础。
- [MeteorNOX/DeepSeek-Balance-Whale-Widget](https://github.com/MeteorNOX/DeepSeek-Balance-Whale-Widget)：DeepSeek 余额气泡思路参考。
