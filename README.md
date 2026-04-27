# AstrBot 跨界通讯器 (Contact Master)

基于 AstrBot v4 的 Function Calling 插件，赋予 LLM **主动联系主人**的能力。

## 功能特性

- **Function Calling 驱动**：AI 会根据对话语境（如"帮我留言给主人"、"通知作者"）自动调用工具。
- **跨界通讯**：支持从群聊或其他平台通过 UMO 协议直接穿透到主人的私聊。
- **上下文回显**：发送成功后会在 Tool Result 中回显内容，让 AI 能够自然地反馈给当前用户。

## 配置说明

在 AstrBot WebUI 的「插件配置」面板中设置，或手动创建 `data/config/astrbot_plugin_contact_master_config.json`：

| 配置项 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `master_uid` | 主人的 QQ 号或平台唯一 ID | `0000000` |

## 安装

1. 在 AstrBot 插件市场搜索 `contact_master` 点击安装。
2. 或将本项目文件夹放入 `data/plugins/` 目录，重启 AstrBot。

## 当前已知限制

由于 **AstrBot 框架架构限制**（相关 issue: #3216），本插件主动发送的消息**不会进入 LLM 的私聊对话历史**。这意味着：

- 主人私聊回复 Bot 时，Bot **无法从上下文中"记起"自己刚才发过什么**。
- Bot 只能通过 Tool Result 回显（本轮提示词内）获知发送内容。
- WebUI 的聊天界面中可以看到发送记录，但 LLM 推理时不会加载。

**这不是 bug，而是目前所有绕过 AstrBot 事件总线的主动消息插件共同面对的限制。** 社区插件 `proactive_chat` 通过自建调度器和历史管理绕过此问题，但 Function Calling 工具在 Agent Loop 内的生命周期不同，无法直接复用该方案。

## 未来可改进方向

欢迎 PR 或讨论：

1. **官方 API 支持**：等待 AstrBot 提供 `send_message_with_history()` 或类似的上下文注入 API（RFC #3497）。届时只需替换一行调用即可解决历史断裂问题。
2. **RAG 记忆补偿**：接入向量记忆插件（如 mem0、astrbot_plugin_context_aware），将发送内容作为"短期事实"写入记忆，供 LLM 后续检索。
3. **主人回复回写**：监听主人私聊回复事件，将回复内容反向注入群聊会话的历史中，实现双向上下文同步。
4. **多主人支持**：将 `master_uid` 扩展为列表，支持通知多个管理员。

## 注意事项

- 请确保适配器（如 LLoneBot、NapCat）具有发送私聊消息的权限。
- 主人需要**先私聊过 Bot**，确保 AstrBot 内部已建立私聊会话，否则 `send_message` 会找不到 platform session。
- 频繁主动私聊可能触发 QQ 风控，建议仅用于紧急通知、报错上报等低频场景。
- 本插件在 AstrBot v4.23.5 + aiocqhttp 环境下测试通过。

## 兼容性

- AstrBot &gt;= v4.22.0
- 平台：aiocqhttp (OneBot 协议)
