plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.f1.trackrecorder"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.f1.trackrecorder"
        minSdk = 26          // Android 8.0 - wide compatibility
        targetSdk = 34       // Android 14
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    // Minimal dependencies - only what's strictly necessary
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    
    // NO Jetpack Compose
    // NO Coroutines
    // NO Room
    // NO Retrofit
    // NO fancy libraries
}
