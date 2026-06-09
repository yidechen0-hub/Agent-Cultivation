package com.sanrenxing.feature.spirit

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sanrenxing.core.model.Spirit
import com.sanrenxing.core.network.api.CreateSpiritRequest
import com.sanrenxing.core.network.api.SpiritApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SpiritListViewModel @Inject constructor(
    private val spiritApi: SpiritApi
) : ViewModel() {

    private val _uiState = MutableStateFlow(SpiritListUiState())
    val uiState: StateFlow<SpiritListUiState> = _uiState.asStateFlow()

    init {
        loadSpirits()
    }

    fun loadSpirits() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            try {
                val spirits = spiritApi.getMySpirits()
                _uiState.update { it.copy(spirits = spirits, isLoading = false) }
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false, error = e.message) }
            }
        }
    }

    fun createSpirit(name: String) {
        viewModelScope.launch {
            try {
                val spirit = spiritApi.createSpirit(CreateSpiritRequest(name))
                _uiState.update { it.copy(spirits = it.spirits + spirit) }
            } catch (e: Exception) {
                _uiState.update { it.copy(error = e.message) }
            }
        }
    }
}

data class SpiritListUiState(
    val spirits: List<Spirit> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)
