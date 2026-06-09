package com.sanrenxing.core.common

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

object RootExecutor {

    suspend fun execute(command: String): Result<String> = withContext(Dispatchers.IO) {
        runCatching {
            val process = Runtime.getRuntime().exec(arrayOf("su", "-c", command))
            val output = process.inputStream.bufferedReader().readText()
            val error = process.errorStream.bufferedReader().readText()
            process.waitFor()
            if (process.exitValue() == 0) output.trim()
            else throw RuntimeException("Root command failed: $error")
        }
    }

    suspend fun isRootAvailable(): Boolean =
        execute("id").getOrNull()?.contains("uid=0") == true

    suspend fun readAppDatabase(packageName: String, dbName: String): File? {
        val srcPath = "/data/data/$packageName/databases/$dbName"
        val destPath = "/data/local/tmp/$dbName"
        execute("cp $srcPath $destPath && chmod 644 $destPath")
        return File(destPath).takeIf { it.exists() }
    }

    suspend fun getForegroundApp(): String? =
        execute("dumpsys activity activities | grep mResumedActivity")
            .getOrNull()
            ?.let { Regex("\\{.*?\\s(\\S+)/").find(it)?.groupValues?.get(1) }

    suspend fun screenshot(path: String): Result<String> =
        execute("screencap -p $path")
}
