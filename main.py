import os
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
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
        
        # 直接调用官方发送接口
        await self.context.send_message(
            master.umo,
            MessageChain([Plain(message)])
        )
        
        # 备用：如果热补丁没生效，手动同步
        if self.auto_sync:
            await sync_proactive_message(self.context, master.umo, message)
        
        return f"已向主人发送：「{message}」"

    # ====================指令：联系人管理====================

    @filter.command("联系人指令")
    async def contact_help(self, event: AstrMessageEvent):
        '''查看通讯录插件的所有指令说明。'''
        help_text = (
            "📞 【跨界通讯器】指令菜单：\n"
            "------------------------\n"
            "1. /添加联系人 <名称> <ID> [别名(逗号分隔)] [消息类型(默认FriendMessage)]\n"
            "   示例：/添加联系人 运维老哥 123456 老哥,ops\n\n"
            "2. /查看联系人\n"
            "   说明：列出当前通讯录中的所有人员\n\n"
            "3. /删除联系人 <名称>\n"
            "   示例：/删除联系人 运维老哥\n\n"
            "4. /联系人帮助\n"
            "   说明：查看此帮助菜单"
        )
        yield event.plain_result(help_text)

    @filter.command("添加联系人")
    async def add_contact(self, event: AstrMessageEvent, name: str, uid: str, 
                         arg1: str = "", arg2: str = "", arg3: str = ""):
        '''添加联系人到通讯录。
        用法：/添加联系人 <名称> <ID> [别名] [群聊/私聊]'''
        
        # 把后面的可选参数收集起来智能分析
        tail_args = [a for a in [arg1, arg2, arg3] if a]
        
        aliases_str = ""
        msg_type = "FriendMessage" # 默认是私聊
        
        # 从后往前找，看看有没有指定消息类型 (容错各种写法)
        if tail_args:
            last_arg = tail_args[-1].lower()
            # 匹配连续写的 GroupMessage 或 群聊
            if last_arg in ["groupmessage", "群聊", "group"]:
                msg_type = "GroupMessage"
                tail_args.pop()
            # 匹配中间加了空格的 Group Message
            elif last_arg == "message" and len(tail_args) >= 2 and tail_args[-2].lower() == "group":
                msg_type = "GroupMessage"
                tail_args.pop()
                tail_args.pop()
            # 匹配连续写的 FriendMessage 或 私聊
            elif last_arg in ["friendmessage", "私聊", "friend"]:
                msg_type = "FriendMessage"
                tail_args.pop()
            # 匹配中间加了空格的 Friend Message
            elif last_arg == "message" and len(tail_args) >= 2 and tail_args[-2].lower() == "friend":
                msg_type = "FriendMessage"
                tail_args.pop()
                tail_args.pop()
                
        # 排除掉类型说明后，剩下的如果还有，就当作别名
        if tail_args:
            aliases_str = ",".join(tail_args)
            
        platform = event.unified_msg_origin.split(":")[0]
        umo = f"{platform}:{msg_type}:{uid}"
        alias_list = [a.strip() for a in aliases_str.split(",") if a.strip()]
        
        self.contact_book.add(Contact(
            name=name, umo=umo, aliases=alias_list,
            platform=platform, msg_type=msg_type, uid=uid
        ))
        
        # 根据类型给不同的 emoji 提示
        icon = "👥" if msg_type == "GroupMessage" else "👤"
        yield event.plain_result(f"✅ {icon} 已成功添加联系人 {name}（{umo}）")

    @filter.command("查看联系人")
    async def list_contacts(self, event: AstrMessageEvent):
        '''列出所有已保存的联系人。
        用法：/查看联系人'''
        contacts = self.contact_book.list_all()
        if not contacts:
            yield event.plain_result("联系人簿目前为空。")
            return
            
        lines = [f"- {c.name} ({', '.join(c.aliases)}) -> {c.umo}" for c in contacts]
        yield event.plain_result("当前联系人簿：\n" + "\n".join(lines))

    @filter.command("删除联系人")
    async def remove_contact(self, event: AstrMessageEvent, name: str):
        '''删除指定联系人。
        用法：/删除联系人 <联系人名称>'''
        if self.contact_book.remove(name):
            yield event.plain_result(f"已删除联系人：{name}。")
        else:
            yield event.plain_result(f"❌ 找不到名为 {name} 的联系人。")
