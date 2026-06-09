package com.sanrenxing.core.model

import kotlinx.serialization.Serializable

@Serializable
data class Battle(
    val id: String,
    val type: String,
    val battleSubject: String,
    val challengerAgentId: String,
    val defenderAgentId: String,
    val status: String,
    val questions: List<Question> = emptyList()
)

@Serializable
data class Question(
    val id: String,
    val type: String,
    val prompt: String,
    val referenceAnswer: String? = null
)

@Serializable
data class BattleResult(
    val battleId: String,
    val winnerId: String?,
    val challengerScore: Int,
    val defenderScore: Int,
    val rounds: List<RoundResult>,
    val analysis: BattleAnalysis
)

@Serializable
data class RoundResult(
    val questionId: String,
    val challengerAnswer: String,
    val defenderAnswer: String,
    val challengerPoints: Float,
    val defenderPoints: Float,
    val comment: String
)

@Serializable
data class BattleAnalysis(
    val weakPoints: List<String>,
    val strongPoints: List<String>,
    val recommendations: List<String>
)
