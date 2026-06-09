pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "AgentCultivation"

include(":app")
include(":core:network")
include(":core:database")
include(":core:datastore")
include(":core:ui")
include(":core:model")
include(":core:common")
include(":feature:spirit")
include(":feature:chat")
include(":feature:battle")
include(":feature:social")
include(":feature:profile")
