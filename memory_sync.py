import json
import types
from astrbot.api import logger


def ensure_memory_api(context) -> bool:
    """在 ConversationManager 上安全挂载记忆注入能力"""
    cm = getattr(context, "conversation_manager", None)
    if not cm:
        return False
    if hasattr(cm, "_contact_master_memory_ready"):
        return True

    async def append_history_messages(self, cid: str, messages: list[dict]) -> None:
        conv = await self.db.get_conversation_by_id(cid=cid)
        if not conv:
            raise Exception(f"Conversation with id {cid} not found")
        
        # 千锤百炼的防御网
        history = getattr(conv, 'content', None)
        if history is None:
            history = getattr(conv, 'history', None)
            
        if isinstance(history, str):
            history = json.loads(history) if history.strip() else []
        elif not isinstance(history, list):
            history = []
            
        history.extend(messages)
        await self.db.update_conversation(cid=cid, content=history)

    cm.append_history_messages = types.MethodType(append_history_messages, cm)
    cm._contact_master_memory_ready = True
    logger.info("[ContactMaster] 记忆注入 API 已安全挂载")
    return True


async def sync_proactive_message(context, umo: str, content: str) -> bool:
    """把主动消息同步到目标会话历史"""
    try:
        cm = getattr(context, "conversation_manager", None)
        
        # ====== 核心修复：自动扣动扳机 ======
        if cm and not hasattr(cm, "append_history_messages"):
            ensure_memory_api(context)
        # ====================================

        if not cm or not hasattr(cm, "append_history_messages"):
            logger.debug(f"[ContactMaster] 记忆注入不可用，跳过同步")
            return False

        conv_id = await cm.get_curr_conversation_id(umo)
        if not conv_id:
            logger.debug(f"[ContactMaster] 会话 {umo} 无当前对话，跳过同步")
            return False

        await cm.append_history_messages(
            cid=conv_id,
            messages=[{"role": "assistant", "content": content}]
        )
        logger.info(f"[ContactMaster] 记忆已同步至 {umo}")
        return True
        
    except Exception as e:
        logger.warning(f"[ContactMaster] 记忆同步失败: {e}")
        return False
