package com.sanrenxing.app.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController

@Composable
fun AppNavHost() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = "spirit_list"
    ) {
        composable("spirit_list") {
            // SpiritListScreen(navController)
        }
        composable("chat/{conversationId}") {
            // ChatScreen()
        }
        composable("battle_hall") {
            // BattleHallScreen(navController)
        }
        composable("battle/{battleId}") {
            // BattleScreen()
        }
        composable("profile") {
            // ProfileScreen()
        }
    }
}
