package com.sanrenxing.core.model

import kotlinx.serialization.Serializable

@Serializable
data class Message(
    val id: String,
    val conversationId: String,
    val role: MessageRole,
    val content: String,
    val createdAt: String
)

@Serializable
enum class MessageRole {
    USER,
    ASSISTANT,
    SYSTEM
}

@Serializable
data class ChatDelta(
    val delta: String = "",
    val finishReason: String? = null
)
