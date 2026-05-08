from astrbot.api import logger


def apply_send_message_enhancement(contact_book, context):
    """
    透明增强官方 send_message_to_user：
    1. 自然语言寻址（昵称 → UMO）
    2. 发送后自动注入历史
    """
    
    # 第一层防护：导入失败不崩溃
    try:
        from astrbot.core.tools.message_tools import SendMessageToUserTool
    except ImportError:
        logger.warning("[ContactMaster] 找不到官方 SendMessageToUserTool，增强未生效")
        return False

    # 第二层防护：属性检查
    if not hasattr(SendMessageToUserTool, "call"):
        logger.warning("[ContactMaster] 官方 SendMessageToUserTool 结构已变更，增强未生效")
        return False

    # 第三层防护：避免重复挂载
    if hasattr(SendMessageToUserTool, "_contact_master_enhanced"):
        logger.debug("[ContactMaster] 增强补丁已挂载，跳过")
        return True

    _original_call = SendMessageToUserTool.call

    async def _enhanced_call(self, context, **kwargs):
        # === 前置增强：自然语言寻址 ===
        session = kwargs.get("session")
        if session and isinstance(session, str):
            # 先查联系人簿
            resolved = contact_book.resolve(session)
            if resolved:
                kwargs["session"] = resolved.umo
                logger.debug(f"[ContactMaster] 联系人解析: '{session}' -> '{resolved.umo}'")
            else:
                # 回退：让官方自己处理（可能是完整 UMO 或裸 ID）
                logger.debug(f"[ContactMaster] 未解析 '{session}'，原样传递给官方工具")

        # === 调用官方原版 ===
        result = await _original_call(self, context, **kwargs)

        # === 后置增强：上下文注入 ===
        # 只处理真正发送成功的情况
        if isinstance(result, str) and result.startswith("Message sent to session"):
            try:
                # 提取目标 UMO（从官方返回值解析）
                # 官方格式: "Message sent to session <UMO>"
                target_umo = result.replace("Message sent to session ", "").strip()
                
                # 生成记忆摘要
                text_fragments = []
                for msg in kwargs.get("messages", []):
                    m_type = str(msg.get("type", "")).lower()
                    if m_type == "plain":
                        text = str(msg.get("text", "")).strip()
                        if text:
                            text_fragments.append(text)
                    elif m_type == "mention_user":
                        uid = msg.get("mention_user_id", "")
                        text_fragments.append(f"[@{uid}]")
                    elif m_type == "image":
                        src = msg.get("path") or msg.get("url") or "unknown"
                        text_fragments.append(f"[Image Sent: {src}]")
                    elif m_type == "record":
                        text_fragments.append("[Voice Record Sent]")
                    elif m_type == "video":
                        src = msg.get("path") or msg.get("url") or "unknown"
                        text_fragments.append(f"[Video Sent: {src}]")
                    elif m_type == "file":
                        name = msg.get("text") or msg.get("path") or "Unknown File"
                        text_fragments.append(f"[File Sent: {name}]")

                if text_fragments:
                    from .memory_sync import sync_proactive_message
                    await sync_proactive_message(
                        context.context.context,
                        target_umo,
                        " ".join(text_fragments)
                    )
            except Exception as e:
                logger.warning(f"[ContactMaster] 发送后记忆同步失败: {e}")
                # 同步失败不影响主流程

        return result

    SendMessageToUserTool.call = _enhanced_call
    SendMessageToUserTool._contact_master_enhanced = True
    logger.info("[ContactMaster] 官方发送工具增强补丁挂载成功")
    return True
