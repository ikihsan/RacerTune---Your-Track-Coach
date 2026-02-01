package com.f1.trackrecorder

import org.json.JSONObject

/**
 * Data classes matching Vertical Slice V1 schema.
 * 
 * These are intentionally simple.
 * No Kotlin data class features beyond what's necessary.
 */

/**
 * Single GPS measurement.
 * 
 * All fields match the V1 schema exactly.
 * Nullable fields are optional per schema.
 */
data class GPSSample(
    val timestamp_ms: Long,        // Unix epoch milliseconds
    val latitude_deg: Double,      // WGS84 latitude [-90, 90]
    val longitude_deg: Double,     // WGS84 longitude [-180, 180]
    val altitude_m: Float?,        // Altitude above sea level (optional)
    val speed_mps: Float,          // Speed in m/s [0, 150]
    val bearing_deg: Float?,       // Heading [0, 360) (optional)
    val accuracy_m: Float,         // Horizontal accuracy in meters
    val satellites: Int?           // Number of satellites (optional)
) {
    fun toJson(): JSONObject {
        return JSONObject().apply {
            put("timestamp_ms", timestamp_ms)
            put("latitude_deg", latitude_deg)
            put("longitude_deg", longitude_deg)
            altitude_m?.let { put("altitude_m", it.toDouble()) }
            put("speed_mps", speed_mps.toDouble())
            bearing_deg?.let { put("bearing_deg", it.toDouble()) }
            put("accuracy_m", accuracy_m.toDouble())
            satellites?.let { put("satellites", it) }
        }
    }
}

/**
 * Single IMU measurement.
 * 
 * Combines accelerometer and gyroscope into one sample.
 * All fields are required per V1 schema.
 */
data class IMUSample(
    val timestamp_ms: Long,        // Unix epoch milliseconds
    val accel_x_mps2: Float,       // Acceleration X axis (device frame) in m/s²
    val accel_y_mps2: Float,       // Acceleration Y axis (device frame) in m/s²
    val accel_z_mps2: Float,       // Acceleration Z axis (device frame) in m/s²
    val gyro_x_rps: Float,         // Angular velocity X axis in rad/s
    val gyro_y_rps: Float,         // Angular velocity Y axis in rad/s
    val gyro_z_rps: Float          // Angular velocity Z axis in rad/s (yaw)
) {
    fun toJson(): JSONObject {
        return JSONObject().apply {
            put("timestamp_ms", timestamp_ms)
            put("accel_x_mps2", accel_x_mps2.toDouble())
            put("accel_y_mps2", accel_y_mps2.toDouble())
            put("accel_z_mps2", accel_z_mps2.toDouble())
            put("gyro_x_rps", gyro_x_rps.toDouble())
            put("gyro_y_rps", gyro_y_rps.toDouble())
            put("gyro_z_rps", gyro_z_rps.toDouble())
        }
    }
}

/**
 * Orientation metadata captured at session start.
 * 
 * Used to transform IMU readings from device frame to vehicle frame.
 */
data class OrientationMetadata(
    val device_orientation: String,           // PORTRAIT, LANDSCAPE_LEFT, LANDSCAPE_RIGHT
    val mount_pitch_deg: Float? = null,       // Estimated pitch angle
    val mount_roll_deg: Float? = null,        // Estimated roll angle
    val gravity_vector: FloatArray            // Gravity direction at calibration
) {
    fun toJson(): JSONObject {
        return JSONObject().apply {
            put("device_orientation", device_orientation)
            mount_pitch_deg?.let { put("mount_pitch_deg", it.toDouble()) }
            mount_roll_deg?.let { put("mount_roll_deg", it.toDouble()) }
            put("gravity_vector", gravity_vector.map { it.toDouble() })
        }
    }
    
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        other as OrientationMetadata
        if (device_orientation != other.device_orientation) return false
        if (mount_pitch_deg != other.mount_pitch_deg) return false
        if (mount_roll_deg != other.mount_roll_deg) return false
        if (!gravity_vector.contentEquals(other.gravity_vector)) return false
        return true
    }
    
    override fun hashCode(): Int {
        var result = device_orientation.hashCode()
        result = 31 * result + (mount_pitch_deg?.hashCode() ?: 0)
        result = 31 * result + (mount_roll_deg?.hashCode() ?: 0)
        result = 31 * result + gravity_vector.contentHashCode()
        return result
    }
}
