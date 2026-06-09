package com.sanrenxing.core.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary = Color(0xFF4A6CF7),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFDBE1FF),
    secondary = Color(0xFF10B981),
    tertiary = Color(0xFFF59E0B),
    background = Color(0xFFF8FAFC),
    surface = Color.White,
    error = Color(0xFFEF4444)
)

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFF8BA4FF),
    onPrimary = Color(0xFF002394),
    primaryContainer = Color(0xFF3350CF),
    secondary = Color(0xFF34D399),
    tertiary = Color(0xFFFBBF24),
    background = Color(0xFF0F172A),
    surface = Color(0xFF1E293B),
    error = Color(0xFFF87171)
)

@Composable
fun AgentCultivationTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}
