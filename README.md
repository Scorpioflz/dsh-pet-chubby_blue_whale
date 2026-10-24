# dsh-pet-selfuse

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
| `dsh-web-service` | REST API 服务（会话/工作区/文件上传/SSE 流式对话） | [toddpan/dsh-webapi](https://github.com/toddpan/dsh-webapi) | DSH Web 自带 |
| `@wycto/dsh-balance-panel` | 余额查询 REST 端点 `GET /dsh-balance-panel` | [wycto/dsh-balance-panel](https://github.com/wycto/dsh-balance-panel) | `dsh plugin --profile web add @wycto/dsh-balance-panel` |

## 目录

- [从源码运行](#从源码运行)
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
