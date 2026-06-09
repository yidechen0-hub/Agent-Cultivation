package com.sanrenxing.feature.chat

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sanrenxing.core.model.AgentMode
import com.sanrenxing.core.model.Message
import com.sanrenxing.core.model.MessageRole

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    viewModel: ChatViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val messages by viewModel.messages.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("AAgent")
                        Text(
                            text = if (uiState.mode == AgentMode.TOOL) "工具模式" else "代理模式",
                            style = MaterialTheme.typography.labelSmall,
                            color = if (uiState.mode == AgentMode.TOOL)
                                MaterialTheme.colorScheme.primary
                            else
                                MaterialTheme.colorScheme.tertiary
                        )
                    }
                },
                actions = {
                    IconButton(onClick = {
                        val newMode = if (uiState.mode == AgentMode.TOOL) AgentMode.PROXY else AgentMode.TOOL
                        viewModel.switchMode(newMode)
                    }) {
                        Icon(
                            imageVector = if (uiState.mode == AgentMode.TOOL)
                                Icons.Default.Build else Icons.Default.Person,
                            contentDescription = "切换模式"
                        )
                    }
                }
            )
        },
        bottomBar = {
            ChatInput(
                enabled = !uiState.isGenerating,
                onSend = { viewModel.sendMessage(it) }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize(),
            reverseLayout = true,
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            if (uiState.streamingContent.isNotEmpty()) {
                item {
                    MessageBubble(
                        content = uiState.streamingContent,
                        isUser = false,
                        isStreaming = true
                    )
                }
            }
            items(messages) { message ->
                MessageBubble(
                    content = message.content,
                    isUser = message.role == MessageRole.USER
                )
            }
        }
    }
}

@Composable
private fun ChatInput(
    enabled: Boolean,
    onSend: (String) -> Unit
) {
    var text by remember { mutableStateOf("") }

    Surface(tonalElevation = 3.dp) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = text,
                onValueChange = { text = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("输入消息...") },
                enabled = enabled,
                maxLines = 4
            )
            Spacer(modifier = Modifier.width(8.dp))
            IconButton(
                onClick = {
                    if (text.isNotBlank()) {
                        onSend(text)
                        text = ""
                    }
                },
                enabled = enabled && text.isNotBlank()
            ) {
                Icon(Icons.Default.Send, contentDescription = "发送")
            }
        }
    }
}

@Composable
private fun MessageBubble(
    content: String,
    isUser: Boolean,
    isStreaming: Boolean = false
) {
    val alignment = if (isUser) Alignment.End else Alignment.Start
    val containerColor = if (isUser)
        MaterialTheme.colorScheme.primary
    else
        MaterialTheme.colorScheme.surfaceVariant

    val contentColor = if (isUser)
        MaterialTheme.colorScheme.onPrimary
    else
        MaterialTheme.colorScheme.onSurfaceVariant

    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = alignment
    ) {
        Surface(
            shape = MaterialTheme.shapes.medium,
            color = containerColor
        ) {
            Text(
                text = content,
                modifier = Modifier.padding(12.dp),
                color = contentColor
            )
        }
    }
}
