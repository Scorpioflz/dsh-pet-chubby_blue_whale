# 对上游代码的修改记录

> 本文档记录所有对原作者 [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop) 代码的修改，便于后续合并上游更新。
>
> **合并策略**：`git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git && git fetch upstream && git merge upstream/main`。冲突时以本文档为参考保留自用改动。

## 标记说明

- **[原作者]**：原作者代码，未修改
- **[自用-新增]**：新增文件，不影响原代码
- **[自用-修改]**：修改了原代码，需注意合并冲突
- **[自用-删除]**：删除了原文件

---

## 一、新增文件（自用-新增）

合并上游时无冲突。

| 文件 | 用途 |
|---|---|
| `pet/dsh_api.py` | DSH Web Service REST API 客户端（工作区/会话/上传/SSE 流式） |
| `pet/chat/dsh_provider.py` | `DshWebApiProvider`（会话 API 连续对话 + 附件上传 + 角色对应会话）+ `ProviderRouter`（按 provider_id 路由） |
| `pet/dsh_workspace.py` | 工作区标题管理：首次启动弹窗询问，存储到 `%APPDATA%/dsh-pet-standalone/dsh_workspace.json` |
| `pet/weather/ip_city.py` | IP 定位城市：优先高德 API（精度高，需 Key），回退免费 API（ip-api.com / ipinfo.io），首次启动弹窗提醒设置默认城市 |
| `docs/MODIFICATIONS.md` | 本文档 |

## 二、修改文件（自用-修改）

合并上游时**可能冲突**，需手动处理。

### 1. `pet/chat/service.py` — 注入 ProviderRouter + 工作区初始化

**修改位置**：`ChatService.__init__`（约行 63-70）

**原代码**：
```python
def __init__(self,provider=None,parent=None):
    super().__init__(parent); self.provider=provider or OpenAICompatibleProvider(); ...
```

**修改后**：
```python
def __init__(self,provider=None,parent=None):
    super().__init__(parent)
    if provider is None:
        from .dsh_provider import ProviderRouter
        provider = ProviderRouter()
    from ..dsh_workspace import ensure_workspace_title
    ensure_workspace_title()
    self.provider=provider; ...
```

**说明**：延迟导入 `ProviderRouter`，按 `config.provider_id` 路由。`ensure_workspace_title()` 首次启动弹窗询问工作区名称。

### 2. `pet/config.py` — 添加 dsh-webapi provider 默认配置

**修改位置**：`_default_chat_data()`（约行 420-451）

**修改内容**：
- `active_provider` 从 `"openai-main"` 改为 `"dsh-webapi"`
- `providers` 字典新增 `"dsh-webapi"` provider：
  ```python
  "dsh-webapi": {
      "name": "DSH Web API",
      "base_url": "http://127.0.0.1:3080/api/v1",
      "chat_path": "/chat/completions",
      "model": "",
      "api_key_ref": "provider/dsh-webapi",
      "api_key": "",
      ...
  }
  ```

### 3. `pet/vision.py` — 截图提问 DSH 分支

**修改位置**：`_post_vision_request()` 开头（约行 332）

**修改内容**：当 `provider_id == "dsh-webapi"` 时，走 DSH 会话 API：
1. 确保工作区存在
2. 复用最近会话或创建新会话（标题"截图提问"）
3. 上传截图（从 `jpeg_bytes` 或 `messages_override` 的 `image_url` 提取 base64）
4. 发送提示（引用截图文件路径）
5. 返回回复文本

**说明**：原 `_post_vision(7_request` 逻辑完整保留，DSH 分支在开头提前 return。

### 4. `pet/window.py` — 看看屏幕 DSH 分支

**修改位置**：`_look_worker()` 开头（约行 3499）

**修改内容**：当 `provider_id == "dsh-webapi"` 时，截图 → 上传到 DSH 会话 → 提问 → 气泡显示。

### 5. `pet/overlay_shell.py` — 看看屏幕 DSH 分支（overlay 版）

**修改位置**：`_look_worker()` 开头（约行 3443）

**修改内容**：与 `window.py` 相同的 DSH 分支，适配 overlay 拓扑。

### 6. `pet/app.py` — 余额查询 DSH 分支 + 启动检查（工作区 + 城市）

**修改位置 1**：`PetApp.start()` 开头（约行 2632）

**修改内容**：启动时用 `QTimer.singleShot(1000ms)` 延迟执行两个检查：
1. **工作区询问**：active provider 是 DSH 时弹窗询问工作区名称
2. **城市检测**：直接检查 `config.get("feature_activation").get("enabled")` 是否包含 `"weather"`（不依赖 freeze 状态），是则 IP 定位弹窗

**修改位置 2**：`show_balance()`（约行 4107）

**修改内容**：当 `provider_id == "dsh-webapi"` 时，调 `GET /dsh-balance-panel` 端点查询余额。

**修改位置 3**：`_quiet_balance_refresh()`（约行 4041）

**修改内容**：灵动岛卡片展开时的静默余额刷新也加 DSH 分支。

**修改位置 4**：新增 `_balance_worker_dsh()` 方法（约行 4189）

**修改内容**：通过 dsh-balance-panel 插件查询余额，解析 JSON 提取余额信息。支持 `quiet` 参数（灵动岛静默刷新不冒泡）。

### 7. `pet/settings_features.py` — 天气功能激活时触发城市检测

**修改位置**：`_save()` 方法（约行 247）

**修改内容**：保存功能激活状态后，如果 `"weather"` 在 enabled 列表中且城市列表为空，立即触发 IP 定位弹窗：
```python
config.set("feature_activation", {"version": CURRENT_VERSION, "enabled": enabled})
if "weather" in enabled:
    cities = config.get("weather_city_list", [])
    if not cities:
        from .weather.ip_city import ensure_weather_city
        ensure_weather_city(config=config)
```

### 8. `pyproject.toml` — Python 3.14 + uv 依赖管理

**修改内容**：
- 新增 `[project]` 部分（name、version、requires-python=">=3.14"、dependencies）
- 新增 `[project.optional-dependencies]` dev 依赖
- ruff `target-version` 从 `"py313"` 改为 `"py314"`

### 8. `requirements.txt` — PySide6 版本放宽

**修改内容**：`PySide6>=6.5,<6.12; sys_platform == "linux"` 和 `PySide6>=6.5; sys_platform != "linux"` 合并为 `PySide6>=6.8`

### 9. `.gitignore` — CodeArts + uv 配置

**修改内容**：末尾新增 `.codearts/`、`.venv/`、`uv.lock`

### 10. `README.md` — 继承声明 + 自用定位 + 精简

**修改内容**：
- 标题改为 `dsh-pet-chubby_blue_whale`
- 新增继承声明和自用定位说明
- 移除 badges、发布状态、下载/安装/升级、AI 对话教程、版本历史、打包发布、开发者与贡献等章节
- 从源码运行改为 uv 方式
- "特别感谢"改为"原作者"

### 11. `tests/test_presentmon_packaging.py` — 删除 CI 测试

**修改内容**：删除 `test_ci_builds_go_through_the_gated_script` 方法（引用已删除的 `.github/workflows/`）

### 12. `tests/test_packaging_keyring_notices.py` — 删除 android 测试

**修改内容**：删除 `ANDROID_EXPORT`/`ANDROID_GRADLE`/`ANDROID_NOTICE` 常量和 `_load_android_exporter`/`test_android_*` 函数

### 13. `pet/pack_download.py` — 素材包下载 URL 顺序反转

**修改位置**：`_download_locked()` 方法（约行 232）

**修改内容**：`for url in part.urls` 改为 `for url in reversed(part.urls)`，代理地址（列表末尾）优先尝试，GitHub 官方最后。

## 三、删除文件（自用-删除）

| 文件/目录 | 原因 |
|---|---|
| `.github/` | 不需要 CI/CD |
) |
| `android/` | 不需要 Android 客户端 |
| `update.json` | 更新功能不需要 |
| `scripts/android_acceptance.py` | android 相关 |
| `scripts/build_android.ps1` | android 相关 |
| `scripts/export_android_assets.py` | android 相关 |
| `scripts/setup_android.ps1` | android 相关 |
| `tests/test_ci_workflows.py` | 引用已删除的 `.github/workflows/` |
| `tests/test_android_assets.py` | 引用已删除的 `android/` |
| `tests/test_android_acceptance.py` | 引用已删除的 `android/` |

## 四、配置说明

### DSH Web API provider 配置

在 `config.json`（或 `config-slot-0.json`）中：

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

| 字段 | 说明 | 默认值 |
|---|---|---|
| `base_url` | DSH Web Service API 地址 | `http://127.0.0.1:3080/api/v1` |
| `chat_path` | OpenAI 兼容端点路径（视觉模型用） | `/chat/completions` |
| `api_key` | DSH API Key（Bearer 鉴权，关闭鉴权时留空） | `""` |
| `model` | DSH 模型（空表示用 DSH 默认模型） | `""` |

### 工作区标题

- 首次启动弹窗询问，存储到 `%APPDATA%/dsh-pet-standalone/dsh_workspace.json`
- 后续启动直接读取文件
- 所有 DSH 会话在此工作区下创建

### 切换回原 AI API 对话

把 `active_provider` 改为 `"openai-main"` 即可恢复原 OpenAI 兼容接口对话。

## 五、DSH 插件依赖

| 插件 | 用途 | 安装 |
|---|---|---|
| `dsh-web-service` | REST API 服务（会话/工作区/文件上传） | DSH Web 自带 |
| `@wycto/dsh-balance-panel` | 余额查询 REST 端点 `GET /dsh-balance-panel` | `dsh plugin --profile web add @wycto/dsh-balance-panel` |

## 六、合并上游更新步骤

```bash
# 1. 添加上游远程
git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git

# 2. 拉取上游更新
git fetch upstream

# 3. 合并上游 main
git merge upstream/main

# 4. 处理冲突（参考本文档的"修改文件"部分）
#    - pet/chat/service.py: 保留 ProviderRouter 注入 + ensure_workspace_title
#    - pet/config.py: 保留 dsh-webapi provider 配置 + active_provider="dsh-webapi"
#    - pet/vision.py: 保留 _post_vision_request DSH 分支
#    - pet/window.py / overlay_shell.py: 保留 _look_worker DSH 分支
#    - pet/app.py: 保留 PetApp.start 城市检测 + show_balance/_quiet_balance_refresh DSH 分支 + _balance_worker_dsh
#    - pyproject.toml: 保留 [project] 部分和 Python 3.14
#    - tests/: 已删除的测试文件如果上游恢复，需重新删除

# 5. 验证
python -c "import ast; ast.parse(open('pet/dsh_api.py').read()); print('OK')"

# 6. 推送
git push origin main
```