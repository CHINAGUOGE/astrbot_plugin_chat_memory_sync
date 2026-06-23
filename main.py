"""
群聊与私聊记忆同步插件

让私聊与群聊共用同一个持久化记忆系统，
以 QQ 号作为区分不同用户的凭据，不影响其他记忆插件。

© 2026 Guoge Studios
"""

import json
import logging

from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.provider.entities import ProviderRequest
from astrbot.core.star import Context
from astrbot.core.star.base import Star
from astrbot.core.star.register.star_handler import (
    register_on_llm_request,
    register_on_waiting_llm_request,
)

logger = logging.getLogger("astrbot")


class ChatMemorySync(Star):
    """群聊与私聊记忆同步插件

    让同一用户的私聊和群聊共用同一个持久化记忆系统，
    以 QQ 号（sender_id）作为区分不同用户的凭据。
    不影响其他记忆插件的正常工作。
    """

    def __init__(self, context: Context, config: dict | None = None) -> None:
        super().__init__(context, config)
        # 统一记忆会话前缀
        self._MEMORY_SESSION_PREFIX = "chat_memory_sync:user"

    async def initialize(self) -> None:
        """插件初始化"""
        logger.info("群聊与私聊记忆同步插件已加载 © 2026 Guoge Studios")

    async def terminate(self) -> None:
        """插件卸载时调用"""
        logger.info("群聊与私聊记忆同步插件已卸载")

    def _build_user_memory_key(self, event: AstrMessageEvent) -> str | None:
        """构造以用户为维度的统一记忆会话 key。

        格式: chat_memory_sync:user:<platform_id>:<sender_id>

        Args:
            event: 消息事件

        Returns:
            统一的会话 key，如果无法获取必要信息则返回 None
        """
        sender_id = event.get_sender_id()
        if not sender_id:
            return None

        platform_id = event.get_platform_id()
        if not platform_id:
            return None

        return f"{self._MEMORY_SESSION_PREFIX}:{platform_id}:{sender_id}"

    @register_on_waiting_llm_request()
    async def on_waiting_llm_request(
        self,
        event: AstrMessageEvent,
    ) -> None:
        """在 LLM 请求排队前修改会话来源。

        此钩子在 build_main_agent 加载对话之前触发，
        通过修改 event.unified_msg_origin 使后续的对话加载
        使用以用户为维度的统一会话，实现私聊与群聊记忆共享。
        """
        user_memory_key = self._build_user_memory_key(event)
        if not user_memory_key:
            return

        original_umo = event.unified_msg_origin
        new_umo = f"{event.get_platform_id()}:memory_sync:{user_memory_key}"

        if original_umo != new_umo:
            event.unified_msg_origin = new_umo
            logger.info(
                f"[ChatMemorySync] 会话重定向(早期): "
                f"{original_umo} -> {new_umo}"
            )

    @register_on_llm_request()
    async def on_llm_request(
        self,
        event: AstrMessageEvent,
        req: ProviderRequest,
    ) -> None:
        """在 LLM 请求时，确保对话指向正确的共享会话。

        如果 on_waiting_llm_request 未能正确修改会话，
        此钩子会替换 req 中已加载的对话为共享会话的对话。
        """
        user_memory_key = self._build_user_memory_key(event)
        if not user_memory_key:
            return

        new_umo = f"{event.get_platform_id()}:memory_sync:{user_memory_key}"

        # 如果 UMO 还没有被修改（早期钩子可能未生效），现在修改
        if event.unified_msg_origin != new_umo:
            event.unified_msg_origin = new_umo
            logger.info(
                f"[ChatMemorySync] 会话重定向(晚期): -> {new_umo}"
            )

        # 强制替换对话为共享会话的对话
        conv_mgr = self.context.conversation_manager
        cid = await conv_mgr.get_curr_conversation_id(new_umo)
        if not cid:
            cid = await conv_mgr.new_conversation(
                new_umo, event.get_platform_id()
            )
        conversation = await conv_mgr.get_conversation(new_umo, cid)
        if conversation:
            req.conversation = conversation
            req.contexts = json.loads(conversation.history)
            logger.info(
                f"[ChatMemorySync] 对话已替换为共享会话: "
                f"cid={conversation.cid}, "
                f"history_len={len(req.contexts)}"
            )
