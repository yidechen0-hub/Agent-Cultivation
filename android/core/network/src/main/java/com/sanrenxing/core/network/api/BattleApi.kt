package com.sanrenxing.core.network.api

import com.sanrenxing.core.model.Battle
import com.sanrenxing.core.model.BattleResult
import retrofit2.http.*

interface BattleApi {

    @POST("battles")
    suspend fun createBattle(@Body request: CreateBattleRequest): Battle

    @POST("battles/{id}/accept")
    suspend fun acceptBattle(@Path("id") battleId: String): Battle

    @GET("battles/{id}")
    suspend fun getBattle(@Path("id") battleId: String): Battle

    @GET("battles/{id}/result")
    suspend fun getBattleResult(@Path("id") battleId: String): BattleResult

    @GET("bounties")
    suspend fun getBounties(
        @Query("type") type: String? = null,
        @Query("page") page: Int = 1,
        @Query("size") size: Int = 20
    ): BountyListResponse
}

@kotlinx.serialization.Serializable
data class CreateBattleRequest(
    val type: String, // "AvA"
    val challengerAgentId: String,
    val defenderAgentId: String,
    val battleSubject: String // "translation", "grammar", "vocabulary"
)

@kotlinx.serialization.Serializable
data class BountyListResponse(
    val bounties: List<BountyDto>,
    val hasMore: Boolean
)

@kotlinx.serialization.Serializable
data class BountyDto(
    val id: String,
    val title: String,
    val type: String,
    val reward: Int,
    val creatorName: String
)
