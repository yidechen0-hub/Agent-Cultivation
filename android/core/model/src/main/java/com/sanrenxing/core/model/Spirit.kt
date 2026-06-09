package com.sanrenxing.core.model

import kotlinx.serialization.Serializable

@Serializable
data class Spirit(
    val id: String,
    val userId: String,
    val name: String,
    val level: Int = 1,
    val exp: Long = 0,
    val skills: List<Skill> = emptyList(),
    val privacyLevel: String = "standard",
    val knowledgeGraph: Map<String, Float> = emptyMap()
)

@Serializable
data class Skill(
    val id: String,
    val name: String,
    val category: String,
    val description: String,
    val proficiency: Float = 0f,
    val isOfficial: Boolean = false
)

@Serializable
enum class AgentMode {
    TOOL,
    PROXY
}
