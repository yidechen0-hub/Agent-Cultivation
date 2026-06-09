package com.sanrenxing.core.database

import androidx.room.Database
import androidx.room.RoomDatabase
import com.sanrenxing.core.database.dao.MessageDao
import com.sanrenxing.core.database.entity.MessageEntity

@Database(
    entities = [MessageEntity::class],
    version = 1,
    exportSchema = true
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun messageDao(): MessageDao
}
