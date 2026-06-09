package com.sanrenxing.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.sanrenxing.app.navigation.AppNavHost
import com.sanrenxing.core.ui.theme.AgentCultivationTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AgentCultivationTheme {
                AppNavHost()
            }
        }
    }
}
