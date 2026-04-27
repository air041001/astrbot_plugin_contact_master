from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Plain
from astrbot.api.all import *
from astrbot.api import logger


@register("contact_master", "air", "大模型 Function Calling 跨界通讯器", "4.0.0")
class ContactMaster(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        # AstrBot 会自动传入解析后的配置，config 就是扁平化的配置字典
        if config is None:
            config = {}
        
        self.master_uid = config.get("master_uid", "")
        
        if not self.master_uid:
            logger.warning("未配置管理员 QQ 号，请在插件配置中设置！")
            self.master_uid = "0000000"
        else:
            logger.info(f"[ContactMaster] 当前配置的管理员 QQ: {self.master_uid}")

    @llm_tool(name="send_message_to_master")
    async def send_message_to_master(self, event: AstrMessageEvent, message: str):
        """
        Send a private message to the master directly. Use this tool immediately when you need to contact the master.
        Args:
            message (string): The message content.
        """
        try:
            logger.info(f"[Function Calling 触发] 尝试发送内容: {message}")
            
            if self.master_uid == "0000000" or not self.master_uid:
                return "通讯器故障: 未配置管理员QQ 号，请设置！"
            
            platform_prefix = event.unified_msg_origin.split(":")[0]
            master_umo = f"{platform_prefix}:FriendMessage:{self.master_uid}"
            
            await self.context.send_message(
                master_umo,
                MessageChain([Plain(message)])
            )
            
            return f"通讯器连接成功！我已向管理员({self.master_uid})发送：「{message}」。请向当前聊天的人汇报！"
            
        except Exception as e:
            logger.error(f"通讯器跨界发送报错: {e}")
            return f"通讯器故障: {e}。请回答群友你现在联系不上管理员。"
