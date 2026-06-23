# 群聊与私聊记忆同步插件

> © 2026 Guoge Studios

## 简介

让私聊与群聊共用同一个持久化记忆系统，以 QQ 号作为区分不同用户的凭据，不影响其他记忆插件的正常工作。

## 功能特性

- 🔄 **记忆共享**: 同一用户的私聊和群聊共享同一个对话记忆
- 🆔 **QQ号识别**: 以 QQ 号（sender_id）作为唯一标识区分不同用户
- 🔌 **无侵入**: 不影响其他记忆插件的正常工作
- 📝 **持久化**: 记忆通过 AstrBot 内置的会话管理系统持久化存储

## 工作原理

插件通过拦截 LLM 请求事件（`on_llm_request`），在消息处理管道的早期阶段将会话重定向到以用户为维度的统一会话：

1. 获取消息发送者的 QQ 号（sender_id）
2. 构造统一的会话 key: `chat_memory_sync:user:<platform_id>:<sender_id>`
3. 将当前消息的 `unified_msg_origin` 重定向到该统一 key
4. AstrBot 的会话管理系统自动处理对话的持久化和恢复

## 支持平台

- `aiocqhttp` (OneBot v11)
- `qq_official` (QQ 官方 API)
- `qq_official_webhook` (QQ 官方 API Webhook)

## 安装

1. 将本插件放置到 `AstrBot/data/plugins/` 目录下
2. 重启 AstrBot 或在 WebUI 中重载插件

## 使用

插件安装后自动生效，无需额外配置。所有来自支持平台的消息都会自动进行记忆同步。

## 注意事项

- 记忆同步以 `platform_id` + `sender_id` 为维度，不同平台的同一 QQ 号不会互相干扰
- 如果需要清除某用户的同步记忆，可以在 AstrBot WebUI 的会话管理中删除对应的 `memory_sync` 会话
- 本插件不修改任何数据库结构，完全依赖 AstrBot 内置的会话管理系统

## 许可

© 2026 Guoge Studios. All rights reserved.
