package com.sanrenxing.feature.chat

import com.sanrenxing.core.database.dao.MessageDao
import com.sanrenxing.core.database.entity.MessageEntity
import com.sanrenxing.core.model.ChatDelta
import com.sanrenxing.core.model.Message
import com.sanrenxing.core.model.MessageRole
import com.sanrenxing.core.network.api.ChatApi
import com.sanrenxing.core.network.api.SendMessageRequest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import javax.inject.Inject

class ChatRepository @Inject constructor(
    private val chatApi: ChatApi,
    private val messageDao: MessageDao,
    private val json: Json
) {

    fun getMessages(conversationId: String): Flow<List<Message>> =
        messageDao.getMessages(conversationId).map { entities ->
            entities.map { it.toMessage() }
        }

    fun sendMessage(conversationId: String, content: String): Flow<ChatDelta> = flow {
        // Save user message locally
        messageDao.insertMessage(
            MessageEntity(
                id = "local_${System.currentTimeMillis()}",
                conversationId = conversationId,
                role = "USER",
                content = content,
                createdAt = System.currentTimeMillis().toString()
            )
        )

        // Stream response from server
        val response = chatApi.sendMessage(conversationId, SendMessageRequest(content))
        val body = response.body() ?: throw RuntimeException("Empty response")

        val fullResponse = StringBuilder()
        body.source().use { source ->
            while (!source.exhausted()) {
                val line = source.readUtf8Line() ?: break
                if (line.startsWith("data: ")) {
                    val data = line.removePrefix("data: ")
                    if (data == "[DONE]") break
                    val delta = json.decodeFromString<ChatDelta>(data)
                    fullResponse.append(delta.delta)
                    emit(delta)
                }
            }
        }

        // Save assistant message locally
        messageDao.insertMessage(
            MessageEntity(
                id = "assistant_${System.currentTimeMillis()}",
                conversationId = conversationId,
                role = "ASSISTANT",
                content = fullResponse.toString(),
                createdAt = System.currentTimeMillis().toString()
            )
        )
    }.flowOn(Dispatchers.IO)

    private fun MessageEntity.toMessage() = Message(
        id = id,
        conversationId = conversationId,
        role = MessageRole.valueOf(role),
        content = content,
        createdAt = createdAt
    )
}
