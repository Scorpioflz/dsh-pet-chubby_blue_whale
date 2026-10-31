# 文档索引

本文件是 `docs/` 与仓库根级文档的**唯一入口索引**。每个文档一行，写明「它是什么」和「什么时候该读它」。

## 新文档入场规则

1. **任何新文档必须在本文登记一行**，否则视为未定义的孤儿文档。
2. **新文档必须与相关文档互链**：正文中至少一处指向它所补充或取代的既有文档。
3. **取代旧文档时**，先在本文登记旧文档与新文档的关系，再考虑是否删除。
4. **有明确生效范围的文档，标题或首段必须写清基线**（分支 / 版本 / 日期 / 实测用例数）。
5. **「何时必读」写触发条件，不写文档摘要**：写成"改 X 之前必读"，不要写成"介绍了 X"。

---

## 根级入口

| 文档 | 一句话内容 | 何时必读 |
|---|---|---|
| [`../README.md`](../README.md) | 主说明（英文）：下载/安装/使用/功能/DSH 插件依赖/changelog。 | 第一次接触项目；查用户可见行为、插件依赖、变更记录。 |
| [`../README_ZH.md`](../README_ZH.md) | 主说明（中文）：同上。 | 同上。 |
| [`../AGENTS.md`](../AGENTS.md) | 工程指南：项目结构、变更纪律、CI 成本纪律、Context pointers 触发表、agent skills 入口。 | 提交任何代码之前；尤其改动碰撞选举、打包、菜单、设置前，先查 Context pointers。 |
| [`../CONTEXT.md`](../CONTEXT.md) | 领域术语表与禁用说法。 | 命名新概念、写设计文档、或需要确认"这个词在本项目里到底指什么"时。 |
| [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) | 第三方素材、组件与随包分发二进制的授权声明。 | 新增/替换动画素材、图标、字体、第三方库时。 |

---

## 构建与发布

| 文档 | 一句话内容 | 何时必读 |
|---|---|---|
| [`ONEDIR_PACKAGING.md`](ONEDIR_PACKAGING.md) | onedir 打包流水线：绿色版 zip + Inno Setup 安装包，随包资产构建门与诚实边界。 | 改 PyInstaller spec、打包资源、`--add-data` 清单、或平台构建脚本时必读。 |
| [`STABLE_BUILDS.md`](STABLE_BUILDS.md) | 稳定版构建冻结记录：受保护文件名、构建隔离规则。 | 改发布/构建工作流时必读。 |

---

## 设置与门禁

| 文档 | 一句话内容 | 何时必读 |
|---|---|---|
| [`SETTINGS-CHANGE-GATES.md`](SETTINGS-CHANGE-GATES.md) | Settings System 的变更门禁：一条设置能否进入设置页的准入条件、以及变更的准出证据要求。 | 新增、移动、重命名、删除或改变任何持久设置之前必读。 |

---

## Agent 联动与 DSH

| 文档 | 一句话内容 | 何时必读 |
|---|---|---|
| [`AGENT_LINK_PROTOCOL.md`](AGENT_LINK_PROTOCOL.md) | Agent 联动统一事件协议与扩展指南：本地文件事件总线、六态词汇、DSH Agent 接入。 | 接入新 Agent、改事件归一（`normalize_event_state`）或六态词汇时。 |
| [`DSH-BRIDGE-PET-EVENT-CONTRACT-2026-09-02.md`](DSH-BRIDGE-PET-EVENT-CONTRACT-2026-09-02.md) | Agent 适配器 → Pet 的事件契约：三层关系与接入约束。 | 新增或修改适配器（`integrations/dsh-pet-bridge/`）、或需要在 Pet 侧复用既有状态处理时。 |

---

## 网络与代理

| 文档 | 一句话内容 | 何时必读 |
|---|---|---|
| [`NETWORK-PROXY-AND-VPN-2026-09-22.md`](NETWORK-PROXY-AND-VPN-2026-09-22.md) | 代理/VPN 影响面清单：歌词取词、edge-tts 语音、余额/识屏/对话各自该不该走代理，附探针与推荐分流配置。 | 改任何联网功能，或用户报「某功能昨天还好好的」时必读。 |

---

## 交付证据

| 文档 | 一句话内容 | 何时必读 |
|---|---|---|
| [`DEV-HANDOVER.md`](DEV-HANDOVER.md) | 交付证据纪律细则（§8.2/§8.3）：每个 PR 必须交付三份证据（修改文件说明 + 性能分析 + 实机运行记录）。 | 写 PR 报告或审查交付完整性时必读。 |
| [`PR-REPORT-TEMPLATE.md`](PR-REPORT-TEMPLATE.md) | PR 报告模板：四个必备章节的结构模板。 | 写新 PR 报告时必读。 |

---

## PR 报告存档

- [非 DSH 后端移除（2026-10-31）](PR-REPORT-NON-DSH-BACKEND-REMOVAL-2026-10-31.md)：移除非 DSH provider（OpenAI 兼容）、桌宠侧人设拼接（system prompt 首发 + 角色扮演 + 记忆引导）、联网搜索、非 DSH agent 联动；后续清理 roleplay 死代码 + 已删除功能测试/docs（净 −1033 行）；新增 `dsh-web-service` 插件安装检测（硬依赖）。改 `pet/chat/`、`pet/agent_link/__init__.py`、`pet/config.py`、`pet/app.py` 时必读。

---

## Agent 工作流文档

| 文档 | 一句话内容 | 何时必读 |
|---|---|---|
| [`agents/issue-tracker.md`](agents/issue-tracker.md) | Issue 与 spec 的 Local Markdown 约定（`.scratch/<feature-slug>/`）。 | 创建或管理 issue/spec 时。 |
| [`agents/triage-labels.md`](agents/triage-labels.md) | 五个规范 triage 状态标签。 | 给 issue 打标签时。 |
| [`agents/domain.md`](agents/domain.md) | 单上下文文档布局：根 `CONTEXT.md` + `docs/adr/`。 | 写 ADR 或领域文档时。 |
| [`agents/handoff.md`](agents/handoff.md) | 未完成多票据工作的 handoff 约定。 | 暂停或恢复多票据工作时。 |

---

## 第三方文档

| 目录 | 内容 |
|---|---|
| [`third_party_doc/`](third_party_doc/) | 引用的第三方插件文档（如 dsh-webapi README）。 |
| [`screenshots/`](screenshots/) | 文档引用的截图。 |
