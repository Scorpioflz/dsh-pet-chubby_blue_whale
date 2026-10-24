# dsh-pet-chubby_blue_whale

> **继承声明**｜基于 [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop)（MIT License, Copyright (c) 2026 Merzlin）个人自用再开发。保留原版权声明（[`LICENSE`](LICENSE)）与第三方声明（[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)）。

## 自用定位

本项目是 **DSH (DeepSeek Harness) 的桌宠前端**，通过 dsh-web-service 插件的会话 API 接入 DSH：

- **对话**：通过 DSH Web Service 会话 API（`/sessions/:id/prompt-stream`）实现连续对话，DSH 侧显示为同一会话
- **角色对应会话**：每个桌宠角色对应独立 DSH 会话（按 system prompt 指纹映射）
- **看看屏幕/截图提问**：截图上传到 DSH 会话（`POST /sessions/:id/files`）→ 提问 → 气泡显示回复
- **余额查询**：通过 dsh-balance-panel 插件查询 DeepSeek 余额
- **IP 定位城市**：首次启动检测城市，提醒设置默认天气城市
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

依赖管理通过 `pyproject.toml`（uv 方式），无需手动 pip install。

## 打包

### 安装包（exe）

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1
```

产物：`dist-onedir\dsh-pet-chubby_blue_whale-setup.exe`（双击安装，免管理员权限）

### 便携版（zip）

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_portable.ps1
```

产物：`dist-onedir\dsh-pet-chubby_blue_whale-portable.zip`（解压即用）

两个脚本共享前置步骤（uv sync → 帧序列生成 → PyInstaller → 重命名），区别仅在最后：
- **安装包**：ISCC 编译 → 删除 portable.zip
- **便携版**：重命名 portable.zip（不跑 ISCC）

**前提**：
- [uv](https://docs.astral.sh/uv/) 已安装
- 安装包需 Inno Setup 7（ISCC 路径在脚本中配置，默认 `D:\Tool\Inno Setup 7\ISCC.exe`）

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

## 功能与设置

### 快速开始

3. 首次使用建议打开「设置」：右键桌宠 → 桌宠设置（或托盘菜单 → 桌宠设置）。设置**关闭即自动保存并立即生效**（直接点 X 也保存）；少数几项要重启或重新登录才生效，清单见[新版设置对话框](#新版设置对话框)。

- **三个例外**（照常保存，但当前进程不按新值跑，行内也写着同一句）：`允许桌宠跨屏` 和 `直播捕获兼容` 要**重启**后生效；`帧率采集权限` 要**注销或重启电脑**后才生效。

### DSH 联动与自启

- 设置中另有「随桌宠启动 dsh 服务」开关与「自启目标」（只影响自启这一路，菜单点哪项就起哪项）：开启后桌宠启动即按目标拉起——目标是 dsh web 时后台静默起服务（不开浏览器、不弹窗口），目标是桌面端界面时直接打开应用；**自启还要求同时开着 DSH 联动**（联动关着时 dsh web 没有消费者，不会拉起）；**关闭开关只是不再自动拉起**，已经在跑的 dsh web 要等桌宠退出或关闭 DSH 联动时才收口（唯一例外：在桌宠拉起探测期间关掉开关，那一次刚拉起的实例会被立刻收掉）；非 Windows 上「自启目标」里的桌面端项置灰并写明原因（暂不支持 ≠ 永远不支持）。

### AI 对话配置

6. Chat 版额外提供「AI 对话」（右键菜单）与「AI 设置」（**托盘菜单**，打开的是设置窗的「AI 与对话」页）入口；无 Chat 版不会显示。

- 视觉模型在「设置 → AI 与对话 → 视觉能力」里配置：可手填模型名/独立端点/独立密钥，或勾选「同聊天模型」复用聊天配置；DeepSeek 聊天模型会自动映射到预览版视觉模型。

- **Ctrl+F 直接搜**：设置窗任意位置按 **Ctrl+F**，光标进侧栏搜索框并全选；回车 / ↓ 前进、↑ 后退（第一条上按 ↑ 回绕到最后一条），命中会切到对应页、展开折叠并高亮。搜索是**跳转式**不是过滤式，不会把人困在空列表里；侧栏的「恢复默认设置 / 保存并退出」是命令、不在搜索范围内。

### 全局快捷键（设置 → 互动 → 快捷键，默认不绑）

> v4.3.4 新增：三个动作各录一个**系统级**组合键，在别的程序前台时也生效。

- 三个动作：**AI 对话**、**看看屏幕**、**截图提问**（与右键菜单同一条入口）。
- **默认全空**，一个键都不绑；右键菜单照常可用。
- **必须带修饰键（Ctrl / Alt / Shift / Win 之一）**：单独一个键会抢走打字输入，所以录入时会被清空（鼠标停在录入框上有说明）。右边的「清除」回到不绑。
- **被别的程序占用时那条不生效**：Windows 的热键表是独占的，日志里能查到失败记录。设置页是独立进程、拿不到注册结果，所以它在行内提前写清后果，不会假装「已生效」。
- **只有 Windows 注册**：其它平台能看能存，但不生效，行内会写明。
- 改完点「保存并退出」即生效，**不用重启**。

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
