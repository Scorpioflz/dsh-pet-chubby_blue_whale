# 对上游代码的修改记录

> 本文档记录所有对原作者 [MerZ# MerZlin/dsh-pet-indesktop](https://&com/MerZlin/dsh-pet-indesktop) 代码的修改，便于后续合并上游更新。
> 
> **合并策略**：上游更新通过 `git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git && git fetch upstream && git merge upstream/main` 合并。冲突时以本文档为参考保留自用改动。

## 标记说明

- **[原作者]**：原作者代码，未修改
- **[自用-新增]**：新增文件，不影响原代码
- **[自用-修改]**：修改了原代码，需注意合并冲突
- **[自用-删除]**：删除了原文件

---

## 一、新增文件（自用-新增）

这些文件是自用版新增的，不影响原代码，合并上游时无冲突。

| 文件 | 用途 |
|---|---|
| `pet/dsh_api.py` | DSH Web Service REST API 客户端（工作区/会话/上传/SSE 流式） |
| `pet/chat/dsh_provider.py` | `DshWebApiProvider`（会话 API 连续对话 + 附件上传）+ `ProviderRouter`（按 provider_id 路由） |
| `docs/MODIFICATIONS.md` | 本文档 |

## 二、修改文件（自用-修改）

这些文件修改了原代码，合并上游时**可能冲突**，需手动处理。

### 1. `pet/chat/service.py` — 注入 ProviderRouter

**修改位置**：`ChatService.__init__`（约行 63-64）

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
    self.provider=provider; ...
```

**说明**：延迟导入 `ProviderRouter`，按 `config.provider_id` 路由到 DSH 或原 OpenAI provider。当 `provider_id != "dsh-webapi"` 时走原逻辑，行为不变。

### 2. `pet/config.py` — 添加 dsh-webapi provider 默认配置

**修改位置**：`_default_chat_data()`（约行 420-451）

**修改内容**：
- `active_provider` 从 `"openai-main"` 改为 `"dsh-webapi"`
- `providers` 字典中新增 `"dsh-webapi"` provider 配置：
  ```python
  "dsh-webapi": {
      "name": "DSH Web API",
      "base_url": "http://127.0.0.1:3080/api/v1",
      "chat_path": "pet",  # DSH 工作区标题
      "model": "",
      "api_key_ref": "provider/dsh-webapi",
      "api_key": "",
      ...
  }
  ```

**说明**：`chat_path` 字段复用为 DSH 工作区标题（对 DSH provider，`chat_path` 不用于端点拼接）。

### 3. `pet/window.py` — 看看屏幕 DSH 分支

**修改位置**：`_look_worker()` 方法开头（约行 3499）

**修改内容**：在方法开头加 DSH 分支，当 `provider.provider_id == "dsh-webapi"` 时走 DSH 路径（截图 → 上传到 DSH 会话 → 提问 → 气泡），否则走原视觉模型路径。

**说明**：原 `_look_worker` 逻辑完整保留，DSH 分支在开头提前 return。

### 4. `pet/overlay_shell.py` — 看看屏幕 DSH 分支（overlay 版）

**修改位置**：`_look_worker()` 方法开头（约行 3443）

**修改内容**：与 `window.py` 相同的 DSH 分支，适配 overlay 拓扑。

### 5. `pyproject.toml` — Python 3.14 + uv 依赖管理

**修改内容**：
- 新增 `[project]` 部分（name、version、requires-python=">=3.14"、dependencies）
- 新增 `[project.optional-dependencies]` dev 依赖
- ruff `target-version` 从 `"py313"` 改为 `"py314"`

### 6. `requirements.txt` — PySide6 版本放宽

**修改内容**：`PySide6>=6.5,<6.12; sys_platform == "linux"` 和 `PySide6>=6.5; sys_platform != "linux"` 合并为 `PySide6>=6.8`

### 7. `.gitignore` — CodeArts + uv 配置

**修改内容**：末尾新增 `.codearts/`、`.venv/`、`uv.lock`

### 8. `README.md` — 继承声明 + 自用定位 + 精简

**修改内容**：
- 标题改为 `dsh-pet-selfuse`
- 新增继承声明和自用定位说明
- 移除 badges、发布状态、下载/安装/升级、AI 对话教程、版本历史、打包发布等章节
- 从源码运行改为 uv 方式

### 9. `tests/test_presentmon_packaging.py` — 删除 CI 测试

**修改内容**：删除 `test_ci_builds_go_through_the_gated_script` 方法（引用已删除的 `.github/workflows/`）

### 10. `tests/test_packaging_keyring_notices.py` — 删除 android 测试

**修改内容**：删除 `ANDROID_EXPORT`/`ANDROID_GRADLE`/`ANDROID_NOTICE` 常量和 `_load_android_exporter`/`test_android_*` 函数

## 三、删除文件（自用-删除）

| 文件/目录 | 原因 |
|---|---|
| `.github/` | 不需要 CI/CD |
| `android/` | 不需要 Android 客户端 |
| `update.json` | 更新功能不需要（dsh-webapi provider 不走更新检查） |
| `scripts/android_acceptance.py` | android 相关 |
| `scripts/build_android.ps1` | android 相关 |
| `scripts/export_android_assets.py` | android 相关 |
| `scripts/setup_android.ps1` | android 相关 |
| `tests/test_ci_workflows.py` | 引用已删除的 `.github/workflows/` |
| `tests/test_android_assets.py` | 引用已删除的 `android/` |
| `tests/test_android_acceptance.py` | 引用已删除的 `android/` |

## 四、配置说明

### DSH Web API 配置

在 `config.json`（或 `config-slot-0.json`）中：

```json
{
  "chat": {
    "active_provider": "dsh-webapi",
    "providers": {
      "dsh-webapi": {
        "name": "DSH Web API",
        "base_url": "http://127.0.0.1:3080/api/v1",
        "chat_path": "pet",
        "api_key": "<你的 DSH API Key>",
        "model": ""
      }
    }
  }
}
```

| 字段 | 说明 | 默认值 |
|---|---|---|
| `base_url` | DSH Web Service API 地址 | `http://127.0.0.1:3080/api/v1` |
| `chat_path` | DSH 工作区标题（复用字段） | `pet` |
| `api_key` | DSH API Key（Bearer 鉴权，关闭鉴权时留空） | `""` |
| `model` | DSH 模型（空表示用 DSH 默认模型） | `""` |

### 切换回原 AI API 对话

把 `active_provider` 改为 `"openai-main"` 即可恢复原 OpenAI 兼容接口对话。

## 五、合并上游更新步骤

```bash
# 1. 添加上游远程
git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git

# 2. 拉取上游更新
git fetch upstream

# 3. 合并上游 main
git merge upstream/main

# 4. 处理冲突（参考本文档的"修改文件"部分）
#    - pet/chat/service.py: 保留 ProviderRouter 注入
#    - pet/config.py: 保留 dsh-webapi provider 配置
#    - pet/window.py / overlay_shell.py: 保留 DSH 分支
#    - pyproject.toml: 保留 [project] 部分和 Python 3.14
#    - tests/: 已删除的测试文件如果上游恢复，需重新删除

# 5. 验证
python -c "import ast; ast.parse(open('pet/dsh_api.py').read()); print('OK')"

# 6. 推送
git push origin main
```