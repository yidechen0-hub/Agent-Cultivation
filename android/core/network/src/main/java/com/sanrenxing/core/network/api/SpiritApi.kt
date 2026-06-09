package com.sanrenxing.core.network.api

import com.sanrenxing.core.model.Spirit
import com.sanrenxing.core.model.Skill
import retrofit2.http.*

interface SpiritApi {

    @POST("spirits")
    suspend fun createSpirit(@Body request: CreateSpiritRequest): Spirit

    @GET("spirits/{id}")
    suspend fun getSpirit(@Path("id") id: String): Spirit

    @GET("spirits")
    suspend fun getMySpirits(): List<Spirit>

    @PUT("spirits/{id}/config")
    suspend fun updateConfig(
        @Path("id") id: String,
        @Body config: UpdateConfigRequest
    ): Spirit

    @POST("spirits/{id}/skills")
    suspend fun installSkill(
        @Path("id") spiritId: String,
        @Body request: InstallSkillRequest
    )

    @DELETE("spirits/{spiritId}/skills/{skillId}")
    suspend fun uninstallSkill(
        @Path("spiritId") spiritId: String,
        @Path("skillId") skillId: String
    )

    @GET("skills")
    suspend fun getAvailableSkills(): List<Skill>
}

@kotlinx.serialization.Serializable
data class CreateSpiritRequest(val name: String)

@kotlinx.serialization.Serializable
data class UpdateConfigRequest(
    val toolPrompt: String? = null,
    val proxyPrompt: String? = null,
    val privacyLevel: String? = null
)

@kotlinx.serialization.Serializable
data class InstallSkillRequest(val skillId: String)
