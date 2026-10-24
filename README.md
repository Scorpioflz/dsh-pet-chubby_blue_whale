# dsh-pet-chubby_blue_whale

> **继承声明**｜基于 [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT License, Copyright (c) 2026 Merzlin）个人自用再开发。保留原版权声明（[`LICENSE`](LICENSE)）与第三方声明（[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)）。

## 自用定位

本项目是 **DSH (DeepSeek Harness) 的桌宠前端**，通过 dsh-web-service 插件的会话 API 接入 DSH：

- **对话**：通过 DSH Web Service 会话 API（`/sessions/:id/prompt-stream`）实现连续对话，DSH 侧显示为同一会话
- **看看屏幕/截图提问**：截图上传到 DSH 会话（`POST /sessions/:id/files`）→ 提问 → 气泡显示回复
- **工作区**：所有对话放在指定 DSH 工作区（默认 "pet"），便于整理与权限管理
- **不发布、无 CI/CD、无 Release**，仅供自行封装使用
- 依赖管理用 uv + `pyproject.toml`（Python 3.14+）
- 上游同步：`git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git && git fetch upstream`

## DSH 插件依赖

本桌宠依赖以下 DSH 插件：

| 插件 | 用途 | 地址 | 安装 |
|---|---|---|---|
| `dsh-web-service` | REST API 服务（会话/工作区/文件上传/SSE 流式对话） | [toddpan/dsh-webapi](https://github.com/toddpan/dsh-webapi) |  `dsh plugin --profile web add @toddpan/dsh-webapi`  |
| `@wycto/dsh-balance-panel` | 余额查询 REST 端点 `GET /dsh-balance-panel` | [wycto/dsh-balance-panel](https://github.com/wycto/dsh-balance-panel) | `dsh plugin --profile web add @wycto/dsh-balance-panel` |

## 目录

- [从源码运行](#从源码运行)
- [打包](#打包)
- [素材包说明](#素材包说明)
- [数据目录](#数据目录)
- [项目来源与素材声明](#项目来源与素材声明)
- [许可证与致谢](#许可证与致谢)

---

## 从源码运行

需要 Python 3.14+。使用 uv 管理依赖与虚拟环境：

```powershell
uv sync                    # 按 pyproject.toml 安装依赖到 .venv
uv run python -m pet       # 启动桌宠
```

也可用传统 pip 方式：`python -m pip install -r requirements.txt && python -m pet`。

## 打包

一键打包（PyInstaller onedir + Inno Setup 安装包）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_chubby_blue_whale.ps1
```

脚本自动完成 4 步：

1. `uv sync` + 安装 PyInstaller
2. PyInstaller onedir 打包（webm-chat 变体）
3. 重命名 exe 为 `dsh-pet-chubby_blue_whale.exe`
4. ISCC 编译安装包（需 Inno Setup 7 在 `D:\Tool\Inno Setup 7`）

产物在 `dist-onedir\` 下：

| 文件 | 说明 |
|---|---|
| `dsh-pet-chubby_blue_whale-setup.exe` | 安装包（双击安装，免管理员权限） |
| `dsh-pet-standalone-webm-chat-portable.zip` | 便携绿色版（解压即用） |
| `dsh-pet-standalone-webm-chat\` | onedir 目录（绿色版 = 整个文件夹） |

**前提**：
- [uv](https://docs.astral.sh/uv/) 已安装
- Inno Setup 7（ISCC 路径在脚本中配置，默认 `D:\Tool\Inno Setup 7\ISCC.exe`）

## 素材包说明

### 仓库素材 vs 素材包

仓库中自带 **106 个 WebM 动画**（`assets/characters/shenshen/videos/`），分布在 click/drag/events/idle/move/random/turn 目录。打包时通过 `convert_frameseq_progress.py` 从 WebM 生成帧序列（WebP），无需额外下载。

`packs-index.json` 中的素材包（core + extra1-6，共 ~1.45GB）是**打包好的帧序列**（WebP 逐帧），与仓库中 106 个 WebM 一一对应，不多不少。素材包是给**安装包用户**用的（没有仓库、不想自己转换的用户）。

### anim/ vs frameseq/ 目录

| 目录 | 来源 | 格式 | 使用场景 |
|---|---|---|---|
| `videos/` | 仓库自带 | WebM 视频 | 源素材（开发调试、GIF 变体） |
| `anim/` | 素材包安装 | WebP 帧序列 | 安装包用户（无源视频，帧序列随包下发） |
| `frameseq/` | `convert_frameseq.py` 生成 | WebP 帧序列 | 有仓库的用户（从 WebM 转换） |

运行时 `library.py` 根据是否有素材包索引决定用哪套：
- **有素材包**（`anim/` 存在）→ 直接用 `anim/` 中的帧序列，不需要 `frameseq/`
- **无素材包** → 从 `videos/` 中的 WebM 自动生成 `frameseq/`（运行时首跑自动供给）

两者**可以共存**，不互相替换。优先用素材包（如果有）。

### 手动导入素材包

设置 → **角色与素材** → 点击 **"从本地文件安装…"** → 选择下载的 zip 文件。

文件名需与发布页一致（如 `shenshen-2.0.0-base-640x360.core.zip`）。安装走与应用内下载完全相同的闸：解压 → 逐帧校验 → 合并索引。

### 帧序列转换

打包时 `build_chubby_blue_whale.ps1` 自动执行 `convert_frameseq_progress.py` 生成帧序列（带进度和 ETA），已有则跳过。被 Ctrl+C 打断后下次运行会跳过已完成的 clip，幂等安全。

## 数据目录

设置与 DSH 会话保存在数据目录里（重装不会丢失）：

| 系统 | 数据目录 |
|---|---|
| Windows | `%APPDATA%/dsh-pet-standalone-<变体>/` |
| macOS | `~/Library/Application Support/dsh-pet-standalone-<变体>/` |
| Linux | `~/.config/dsh-pet-standalone-<变体>/` |

目录中主要包含：

```text
config.json                # 全局设置
config-slot-0.json         # 主宠的每宠设置
sessions/<character_id>/   # 会话历史
pet.log
```

## 项目来源与素材声明

**上游代码**来自原作者 [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT License, Copyright (c) 2026 Merzlin）。桌宠的基础功能（窗口、动画、菜单、设置、功能概览、使用教程等）完整来自上游，详见 [上游 README](https://github.com/MerZlin/dsh-pet-indesktop#readme)。

**自用版改动**详见 [`docs/MODIFICATIONS.md`](docs/MODIFICATIONS.md)，核心改造：

- 通过 dsh-web-service 会话 API 接入 DSH（连续对话 + 附件上传 + 工作区管理）
- 看看屏幕/截图提问改为通过 DSH 对话处理
- Python 3.14 + uv 依赖管理

第三方素材与组件授权声明见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## 许可证与致谢

本项目采用 **MIT License**（见仓库根目录 `LICENSE`），第三方素材与组件授权声明见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

**原作者：**

- [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT License, Copyright (c) 2026 Merzlin）：本项目基于此开源项目个人自用再开发。
- [PC2005-cloud/dsh-pet](https://github.com/PC2005-cloud/dsh-pet)：原作者参考的动画素材基础。
- [MeteorNOX/DeepSeek-Balance-Whale-Widget](https://github.com/MeteorNOX/DeepSeek-Balance-Whale-Widget)：DeepSeek 余额气泡思路参考。
