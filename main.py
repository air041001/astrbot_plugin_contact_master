import os
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Plain
from astrbot.api.all import *
from astrbot.api import logger

from .contact_book import ContactBook, Contact
from .tool_enhancer import apply_send_message_enhancement
from .memory_sync import sync_proactive_message


@register("contact_master", "air", "AstrBot 智能联系人网关", "5.0.0")
class ContactMaster(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        if config is None:
            config = {}

        self.master_uid = config.get("master_uid", "")
        self.auto_sync = config.get("auto_sync_history", True)
        
        # 数据目录
        self.data_dir = os.path.join(
            context.get_data_dir(), "contact_master"
        ) if hasattr(context, "get_data_dir") else "./data/contact_master"
        
        # 初始化子系统
        self.contact_book = ContactBook(self.data_dir)
        
        # 挂载增强补丁（防御性：失败不崩溃）
        apply_send_message_enhancement(self.contact_book, context)
        
        # 自动注册主人
        if self.master_uid and self.master_uid != "0000000":
            self._register_master(context)
        
        logger.info(f"[ContactMaster] 已加载 {len(self.contact_book.contacts)} 个联系人")

    def _register_master(self, context: Context):
        """从配置自动注册主人到联系人簿"""
        raw = self.master_uid
        
        # 解析各种格式：完整 UMO / 平台:ID / 纯 ID
        if raw.count(":") >= 2:
            umo = raw
            parts = raw.split(":")
            platform, msg_type, uid = parts[0], parts[1], parts[2]
        elif raw.count(":") == 1:
            platform, uid = raw.split(":")
            msg_type = "FriendMessage"
            umo = f"{platform}:{msg_type}:{uid}"
        else:
            # 默认用 default 平台
            platform, msg_type, uid = "default", "FriendMessage", raw
            umo = f"{platform}:{msg_type}:{uid}"

        self.contact_book.add(Contact(
            name="主人",
            umo=umo,
            aliases=["master", "admin", "老板", "管理员", "作者"],
            platform=platform,
            msg_type=msg_type,
            uid=uid,
        ), persist=False)

    # ==================== 工具：快捷联系主人 ====================

    @llm_tool(name="contact_master")
    async def contact_master(self, event: AstrMessageEvent, message: str):
        """
        快速联系主人。当需要紧急通知、报错上报或私聊沟通时使用。
        Args:
            message (string): 要告诉主人的内容。
        """
        master = self.contact_book.resolve("主人")
        if not master:
            return "通讯器故障：未配置主人信息，请在插件设置中填写 master_uid。"
        
        # 直接调用官方发送接口（会被热补丁增强）
        await self.context.send_message(
            master.umo,
            MessageChain([Plain(message)])
        )
        
        # 备用：如果热补丁没生效，手动同步
        if self.auto_sync:
            await sync_proactive_message(self.context, master.umo, message)
        
        return f"已向主人发送：「{message}」"

    # ==================== 工具：联系人管理 ====================

    @llm_tool(name="add_contact")
    async def add_contact(self, event: AstrMessageEvent, name: str, uid: str, 
                         aliases: str = "", msg_type: str = "FriendMessage"):
        """
        添加联系人到通讯录。添加后可用昵称直接发送消息。
        Args:
            name (string): 显示名称，如"运维小王"。
            uid (string): 平台用户ID（QQ号等）。
            aliases (string): 别名，逗号分隔，如"小王,ops"。
            msg_type (string): FriendMessage 或 GroupMessage。
        """
        platform = event.unified_msg_origin.split(":")[0]
        umo = f"{platform}:{msg_type}:{uid}"
        alias_list = [a.strip() for a in aliases.split(",") if a.strip()]
        
        self.contact_book.add(Contact(
            name=name, umo=umo, aliases=alias_list,
            platform=platform, msg_type=msg_type, uid=uid
        ))
        return f"已添加联系人 {name}（{umo}）"

    @llm_tool(name="list_contacts")
    async def list_contacts(self, event: AstrMessageEvent):
        """列出所有已保存的联系人。"""
        contacts = self.contact_book.list_all()
        if not contacts:
            return "联系人簿为空。"
        lines = [f"- {c.name} ({', '.join(c.aliases)}) -> {c.umo}" for c in contacts]
        return "联系人簿：\n" + "\n".join(lines)

    @llm_tool(name="remove_contact")
    async def remove_contact(self, event: AstrMessageEvent, name: str):
        """
        删除指定联系人。
        Args:
            name (string): 要删除的联系人名称。
        """
        if self.contact_book.remove(name):
            return f"已删除 {name}。"
        return f"联系人 {name} 不存在。"
