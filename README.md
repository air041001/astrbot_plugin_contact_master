# AstrBot 通讯增强补丁 (Contact Master) v5.0.0

> **一个为了治好大模型“失忆症”而诞生的隐形补丁。**

## 起源

起初，我写这个插件只是为了加个能随时给主人发消息的快捷工具contact_master。但在折腾的过程中，我发现AstrBot官方是有`send_message_to_user`的发送消息的工具，但它有一个让人非常头疼的点：

**bot主动发完消息后，有时会忘了自己发了什么**
如果你问它刚才发了什么，它经常会犯傻地回答：“系统显示发送成功了，但我看不到具体内容哦~”虽然这个工具后续重复测试其实是消息被包裹在tool call中[“#8051”](https://github.com/AstrBotDevs/AstrBot/issues/8051)，在人设作用不强的情况下能读取到发送内容，但对上下文融入并不强，为了彻底治好这个“发信失忆症”，同时避免大模型调用工具时产生混，我把这个插件重构成了一个**官方工具的透明增强补丁**，**主要目的还是优化官方send_messgae_to_user工具的使用方式**。

---

## 一点特色:

### 1. 治好了大模型的“失忆症”

官方原版工具只管把消息发出去，却忘了在对话历史里留底。本插件在底层悄悄打了个补丁：只要消息发送成功，就会把发送的具体内容写入大模型的记忆数据库里。
现在，它不仅清楚地知道自己发了什么，而且完美兼容了某些长期记忆插件

### 2. 重点功能：说人话，别背 UMO (自动解析自然语言为UMO格式)

原版的发信工具需要大模型记住极其复杂的 UMO 格式（比如 `default:FriendMessage:123456`），不好记而且每次都得输入完整格式。
现在，你可以直接让大模型把群友存为联系人。以后只需要说：“给 **小王** 发个消息说我晚点到。”底层会自动把“小王”翻译成正确的 UMO 发出去。
同时，支持联系人添加与删除。

### 3. 专属的主人通知渠道

依然保留了之前做的contact_master工具。如果遇到了什么紧急报错，bot还是可以通过专属通道第一时间呼叫你。

---

## 它是怎么工作的？(一点点技术细节)

* **无感增强**：你和bot都不需要改变习惯，继续用官方的 `send_message_to_user` 工具就行。本插件会在后台默默帮你把 UMO 翻译好，并在发送后把记忆塞进数据库。
---

## 安装

**安装与配置：**

1. 把插件装进你的 AstrBot `plugins` 目录。
2. 去 WebUI 的插件配置里填上你的 `master_uid`（填你的纯 QQ 号或者完整 UMO 都行）。

**使用方法：**

* 呼叫主人：“联系一下主人，就说测试跑通了。”
<img width="797" height="255" alt="image" src="https://github.com/user-attachments/assets/f80f00d0-7ace-4eb3-85f1-22d5f3effdeb" />

* 存联系人：/添加联系人 名字 qq号 群聊类型（不写默认私聊）
<img width="647" height="183" alt="image" src="https://github.com/user-attachments/assets/becbc6c3-643f-4d39-a13a-a9e1b22b5ee0" />
<img width="643" height="131" alt="image" src="https://github.com/user-attachments/assets/f64f325c-5dae-4d6f-ade1-c1df1e265f73" />

* 给别人发信：“用主动发送工具，给 运维老哥 发一句：服务器好像卡了。”
<img width="647" height="180" alt="image" src="https://github.com/user-attachments/assets/6b0644f4-82c3-4e7c-872b-de89afa2882e" />
<img width="434" height="329" alt="image" src="https://github.com/user-attachments/assets/62b36208-34ef-46e0-91b0-c90400ef9dcc" />

* 看通讯录：/查看联系人
<img width="650" height="241" alt="image" src="https://github.com/user-attachments/assets/c1b948e2-a726-4efe-ad0d-c0113e40c901" />

## 配置说明

在 AstrBot WebUI 的「插件配置」面板中设置，或手动创建 `data/config/astrbot_plugin_contact_master_config.json`：

| 配置项 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `master_uid` | 主人的 QQ 号或平台唯一 ID | `0000000` |

## 未来可改进方向

欢迎 PR 或讨论：

1. **多主人支持**：将 `master_uid` 扩展为列表，支持通知多个管理员。

2.**自动获取平台实例名**：目前默认umo开头为default，反正没人用先不做了。

3.**contact_master,send_message_to_user工具硬指令触发**:不论是我的还是官方的都是由自然语言触发，有时很容易受bot人设影响而无法使用，后续考虑增加新的硬指令强制触发

---

**最后：**
写这个 v5.0.0 踩了不少坑，如果它刚好也解决了你遇到的上下文断层问题，欢迎点个 Star！有 Bug 随时提 Issue！但其实我还有很多场景没有测试。。
你要问能直接发消息的前提下搞间接发送有什么意义？可能只是为了一些话从会突然从bot口中说出来的一种小惊喜或仪式感吧，毕竟灵感来源只是朋友的一句“帮我问问空气今天吃什么”
---


## 注意事项

- 请确保适配器（如 LLoneBot、NapCat）具有发送私聊消息的权限。
- 主人需要**确定Bot与联系人有过对话记录**，确保 AstrBot 内部已建立私聊会话，否则 `send_message` 会找不到 platform session。
- 频繁主动私聊可能触发 QQ 风控，建议仅用于紧急通知、报错上报等低频场景。虽然我是当传话筒使的
- 本插件在 AstrBot v4.24.2 + aiocqhttp 环境下测试通过。

## 兼容性

- AstrBot >= v4.24.2
- 平台：aiocqhttp (OneBot 协议)
