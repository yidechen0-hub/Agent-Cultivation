package com.sanrenxing.core.network.api

import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.*

interface ChatApi {

    @POST("conversations")
    suspend fun createConversation(@Body request: CreateConversationRequest): ConversationResponse

    @Streaming
    @POST("conversations/{id}/messages")
    suspend fun sendMessage(
        @Path("id") conversationId: String,
        @Body request: SendMessageRequest
    ): Response<ResponseBody>

    @GET("conversations/{id}/messages")
    suspend fun getMessages(
        @Path("id") conversationId: String,
        @Query("page") page: Int = 1,
        @Query("size") size: Int = 20
    ): MessageListResponse
}

@kotlinx.serialization.Serializable
data class CreateConversationRequest(
    val targetAgentId: String,
    val mode: String // "tool" or "proxy"
)

@kotlinx.serialization.Serializable
data class ConversationResponse(
    val id: String,
    val targetAgentId: String,
    val mode: String
)

@kotlinx.serialization.Serializable
data class SendMessageRequest(val content: String)

@kotlinx.serialization.Serializable
data class MessageListResponse(
    val messages: List<MessageDto>,
    val hasMore: Boolean
)

@kotlinx.serialization.Serializable
data class MessageDto(
    val id: String,
    val role: String,
    val content: String,
    val createdAt: String
)
