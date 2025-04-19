plugins {
    id("com.android.application")
    // START: FlutterFire Configuration
    id("com.google.gms.google-services") // Required for Firebase
    // END: FlutterFire Configuration
    id("kotlin-android")
    id("dev.flutter.flutter-gradle-plugin") // Must be last
}

android {
    namespace = "com.example.cv_flutter"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = "27.0.12077973"

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
        isCoreLibraryDesugaringEnabled = true
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_11.toString()
    }

    defaultConfig {
        applicationId = "com.example.cv_flutter"
        minSdk = 21
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

flutter {
    source = "../.."
}

dependencies {
    // 🔔 Required for FCM support
    implementation("com.google.firebase:firebase-messaging:23.1.2")

    // ✅ Flutter local notifications for custom sound + vibration
    implementation("com.google.firebase:firebase-analytics-ktx") // Optional: for analytics
    implementation("androidx.core:core-ktx:1.10.1")

    // 🔁 Core library desugaring support
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.0.4")
}
