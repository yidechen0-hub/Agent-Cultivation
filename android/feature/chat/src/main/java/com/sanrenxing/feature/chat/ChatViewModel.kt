package com.sanrenxing.feature.chat

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sanrenxing.core.model.AgentMode
import com.sanrenxing.core.model.ChatDelta
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val conversationId: String = savedStateHandle["conversationId"] ?: ""

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    val messages = chatRepository.getMessages(conversationId)
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())

    fun sendMessage(content: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isGenerating = true, streamingContent = "") }

            chatRepository.sendMessage(conversationId, content)
                .catch { e ->
                    _uiState.update { it.copy(isGenerating = false, error = e.message) }
                }
                .collect { delta ->
                    when {
                        delta.finishReason != null -> {
                            _uiState.update { it.copy(isGenerating = false, streamingContent = "") }
                        }
                        else -> {
                            _uiState.update { it.copy(
                                streamingContent = it.streamingContent + delta.delta
                            )}
                        }
                    }
                }
        }
    }

    fun switchMode(mode: AgentMode) {
        _uiState.update { it.copy(mode = mode) }
    }
}

data class ChatUiState(
    val isGenerating: Boolean = false,
    val streamingContent: String = "",
    val error: String? = null,
    val mode: AgentMode = AgentMode.TOOL
)
