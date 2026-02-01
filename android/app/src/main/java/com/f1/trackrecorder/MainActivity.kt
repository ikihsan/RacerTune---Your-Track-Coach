package com.f1.trackrecorder

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.*
import kotlin.math.abs

/**
 * Minimal Sensor Recorder for Vertical Slice V1
 * 
 * Purpose: Record GPS + IMU data to JSON file
 * Philosophy: Simple, Correct, Observable
 * 
 * This is NOT production code. This is a reality check.
 */
class MainActivity : AppCompatActivity(), LocationListener, SensorEventListener {

    companion object {
        private const val TAG = "TrackRecorder"
        private const val PERMISSION_REQUEST_CODE = 1001
        
        // Minimum acceptable rates
        private const val MIN_GPS_RATE_HZ = 1.0
        private const val MIN_IMU_RATE_HZ = 25.0
        
        // Timestamp conversion: nanoseconds to milliseconds
        // Android sensor timestamps are in nanoseconds since boot
        // We need Unix epoch milliseconds
        private var bootTimeMillis: Long = 0
    }

    // =========================================================================
    // STATE
    // =========================================================================
    
    enum class RecordingState {
        IDLE,
        RECORDING,
        STOPPING,
        ERROR
    }
    
    private var state: RecordingState = RecordingState.IDLE
    
    // =========================================================================
    // SENSOR MANAGERS
    // =========================================================================
    
    private lateinit var locationManager: LocationManager
    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null
    private var gyroscope: Sensor? = null
    
    // =========================================================================
    // DATA BUFFERS
    // =========================================================================
    
    private val gpsSamples = mutableListOf<GPSSample>()
    private val imuSamples = mutableListOf<IMUSample>()
    
    // Temporary storage for combining accel + gyro into single IMU sample
    private var lastAccelTimestampNs: Long = 0
    private var lastAccelValues: FloatArray? = null
    private var lastGyroTimestampNs: Long = 0
    private var lastGyroValues: FloatArray? = null
    
    // =========================================================================
    // SESSION METADATA
    // =========================================================================
    
    private var sessionId: String = ""
    private var startTimestampMs: Long = 0
    private var endTimestampMs: Long = 0
    
    // Orientation captured at start
    private var orientationGravityVector: FloatArray? = null
    
    // =========================================================================
    // UI ELEMENTS
    // =========================================================================
    
    private lateinit var tvStatus: TextView
    private lateinit var tvGpsStatus: TextView
    private lateinit var tvImuStatus: TextView
    private lateinit var tvGpsCount: TextView
    private lateinit var tvImuCount: TextView
    private lateinit var tvDuration: TextView
    private lateinit var tvLastFile: TextView
    private lateinit var btnStartStop: Button
    
    // =========================================================================
    // TIMING
    // =========================================================================
    
    private val uiHandler = Handler(Looper.getMainLooper())
    private val uiUpdateRunnable = object : Runnable {
        override fun run() {
            updateUI()
            if (state == RecordingState.RECORDING) {
                uiHandler.postDelayed(this, 500)
            }
        }
    }
    
    // Track rates
    private var lastGpsTimestampMs: Long = 0
    private var lastImuTimestampMs: Long = 0
    private var gpsGapWarningCount = 0
    private var imuGapWarningCount = 0

    // =========================================================================
    // LIFECYCLE
    // =========================================================================
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Calculate boot time for timestamp conversion
        // System.currentTimeMillis() = Unix epoch ms
        // SystemClock.elapsedRealtime() = ms since boot
        bootTimeMillis = System.currentTimeMillis() - SystemClock.elapsedRealtime()
        
        initUI()
        initSensors()
        checkPermissions()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        if (state == RecordingState.RECORDING) {
            stopRecording()
        }
    }
    
    // =========================================================================
    // UI INITIALIZATION
    // =========================================================================
    
    private fun initUI() {
        tvStatus = findViewById(R.id.tvStatus)
        tvGpsStatus = findViewById(R.id.tvGpsStatus)
        tvImuStatus = findViewById(R.id.tvImuStatus)
        tvGpsCount = findViewById(R.id.tvGpsCount)
        tvImuCount = findViewById(R.id.tvImuCount)
        tvDuration = findViewById(R.id.tvDuration)
        tvLastFile = findViewById(R.id.tvLastFile)
        btnStartStop = findViewById(R.id.btnStartStop)
        
        btnStartStop.setOnClickListener {
            when (state) {
                RecordingState.IDLE -> startRecording()
                RecordingState.RECORDING -> stopRecording()
                RecordingState.STOPPING -> { /* ignore */ }
                RecordingState.ERROR -> {
                    state = RecordingState.IDLE
                    updateUI()
                }
            }
        }
        
        updateUI()
    }
    
    private fun updateUI() {
        runOnUiThread {
            tvStatus.text = "State: $state"
            
            when (state) {
                RecordingState.IDLE -> {
                    btnStartStop.text = "START RECORDING"
                    btnStartStop.isEnabled = true
                    tvGpsStatus.text = "GPS: Inactive"
                    tvImuStatus.text = "IMU: Inactive"
                }
                RecordingState.RECORDING -> {
                    btnStartStop.text = "STOP RECORDING"
                    btnStartStop.isEnabled = true
                    tvGpsStatus.text = "GPS: Active"
                    tvImuStatus.text = "IMU: Active"
                    tvGpsCount.text = "GPS Samples: ${gpsSamples.size}"
                    tvImuCount.text = "IMU Samples: ${imuSamples.size}"
                    
                    val durationSec = (System.currentTimeMillis() - startTimestampMs) / 1000.0
                    tvDuration.text = "Duration: ${String.format("%.1f", durationSec)}s"
                }
                RecordingState.STOPPING -> {
                    btnStartStop.text = "SAVING..."
                    btnStartStop.isEnabled = false
                }
                RecordingState.ERROR -> {
                    btnStartStop.text = "ERROR - TAP TO RESET"
                    btnStartStop.isEnabled = true
                }
            }
        }
    }
    
    // =========================================================================
    // SENSOR INITIALIZATION
    // =========================================================================
    
    private fun initSensors() {
        locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        gyroscope = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)
        
        if (accelerometer == null) {
            Log.e(TAG, "No accelerometer available")
        }
        if (gyroscope == null) {
            Log.e(TAG, "No gyroscope available")
        }
    }
    
    // =========================================================================
    // PERMISSIONS
    // =========================================================================
    
    private fun checkPermissions() {
        val permissions = arrayOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
        
        val notGranted = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        
        if (notGranted.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, notGranted.toTypedArray(), PERMISSION_REQUEST_CODE)
        }
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            val allGranted = grantResults.all { it == PackageManager.PERMISSION_GRANTED }
            if (!allGranted) {
                Log.e(TAG, "Location permission denied")
                tvStatus.text = "ERROR: Location permission required"
            }
        }
    }
    
    // =========================================================================
    // RECORDING CONTROL
    // =========================================================================
    
    private fun startRecording() {
        if (state != RecordingState.IDLE) {
            Log.w(TAG, "Cannot start recording in state: $state")
            return
        }
        
        Log.i(TAG, "Starting recording...")
        
        // Clear previous data
        gpsSamples.clear()
        imuSamples.clear()
        lastAccelValues = null
        lastGyroValues = null
        gpsGapWarningCount = 0
        imuGapWarningCount = 0
        
        // Generate session ID
        sessionId = UUID.randomUUID().toString()
        startTimestampMs = System.currentTimeMillis()
        
        // Capture initial gravity vector for orientation
        captureOrientationMetadata()
        
        // Register GPS listener
        if (!registerGpsListener()) {
            state = RecordingState.ERROR
            updateUI()
            return
        }
        
        // Register IMU listeners
        if (!registerImuListeners()) {
            unregisterGpsListener()
            state = RecordingState.ERROR
            updateUI()
            return
        }
        
        state = RecordingState.RECORDING
        uiHandler.post(uiUpdateRunnable)
        updateUI()
        
        Log.i(TAG, "Recording started. Session ID: $sessionId")
    }
    
    private fun stopRecording() {
        if (state != RecordingState.RECORDING) {
            Log.w(TAG, "Cannot stop recording in state: $state")
            return
        }
        
        Log.i(TAG, "Stopping recording...")
        state = RecordingState.STOPPING
        updateUI()
        
        endTimestampMs = System.currentTimeMillis()
        
        // Unregister listeners FIRST
        unregisterGpsListener()
        unregisterImuListeners()
        
        // Stop UI updates
        uiHandler.removeCallbacks(uiUpdateRunnable)
        
        // Write file
        val filename = writeSessionFile()
        
        if (filename != null) {
            tvLastFile.text = "Last file: $filename"
            Log.i(TAG, "Session saved: $filename")
        } else {
            tvLastFile.text = "ERROR: Failed to save"
            Log.e(TAG, "Failed to save session")
        }
        
        state = RecordingState.IDLE
        updateUI()
    }
    
    // =========================================================================
    // ORIENTATION METADATA
    // =========================================================================
    
    private fun captureOrientationMetadata() {
        // Use gravity sensor or accelerometer to get gravity vector
        val gravitySensor = sensorManager.getDefaultSensor(Sensor.TYPE_GRAVITY)
        
        if (gravitySensor != null) {
            // Register briefly to get gravity
            val gravityListener = object : SensorEventListener {
                override fun onSensorChanged(event: SensorEvent?) {
                    event?.let {
                        orientationGravityVector = it.values.clone()
                        sensorManager.unregisterListener(this)
                    }
                }
                override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
            }
            sensorManager.registerListener(gravityListener, gravitySensor, SensorManager.SENSOR_DELAY_NORMAL)
            
            // Wait briefly for gravity reading
            Thread.sleep(100)
            sensorManager.unregisterListener(gravityListener)
        }
        
        if (orientationGravityVector == null) {
            // Fallback: assume device is level
            orientationGravityVector = floatArrayOf(0f, 0f, -9.81f)
            Log.w(TAG, "Could not capture gravity vector, using default")
        }
    }
    
    // =========================================================================
    // GPS LISTENER
    // =========================================================================
    
    private fun registerGpsListener(): Boolean {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) 
            != PackageManager.PERMISSION_GRANTED) {
            Log.e(TAG, "GPS permission not granted")
            return false
        }
        
        try {
            // Request updates as fast as possible
            // minTimeMs = 0 means as fast as available
            // minDistanceM = 0 means every update
            locationManager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                0L,  // minTimeMs
                0f,  // minDistanceM
                this,
                Looper.getMainLooper()
            )
            Log.i(TAG, "GPS listener registered")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to register GPS listener: ${e.message}")
            return false
        }
    }
    
    private fun unregisterGpsListener() {
        try {
            locationManager.removeUpdates(this)
            Log.i(TAG, "GPS listener unregistered")
        } catch (e: Exception) {
            Log.e(TAG, "Error unregistering GPS listener: ${e.message}")
        }
    }
    
    override fun onLocationChanged(location: Location) {
        if (state != RecordingState.RECORDING) return
        
        val timestampMs = location.time  // Already Unix epoch milliseconds
        
        // Check for GPS gaps
        if (lastGpsTimestampMs > 0) {
            val gapMs = timestampMs - lastGpsTimestampMs
            if (gapMs > 2000) {  // > 2 seconds
                gpsGapWarningCount++
                Log.w(TAG, "GPS gap detected: ${gapMs}ms (warning #$gpsGapWarningCount)")
            }
        }
        lastGpsTimestampMs = timestampMs
        
        // Check accuracy
        if (location.accuracy > 25) {
            Log.w(TAG, "Low GPS accuracy: ${location.accuracy}m")
        }
        
        val sample = GPSSample(
            timestamp_ms = timestampMs,
            latitude_deg = location.latitude,
            longitude_deg = location.longitude,
            altitude_m = if (location.hasAltitude()) location.altitude.toFloat() else null,
            speed_mps = if (location.hasSpeed()) location.speed else 0f,
            bearing_deg = if (location.hasBearing()) location.bearing else null,
            accuracy_m = location.accuracy,
            satellites = null  // Not easily available without GnssStatus
        )
        
        synchronized(gpsSamples) {
            gpsSamples.add(sample)
        }
    }
    
    // Deprecated but required by interface
    @Deprecated("Deprecated in API")
    override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
    override fun onProviderEnabled(provider: String) {
        Log.i(TAG, "GPS provider enabled: $provider")
    }
    override fun onProviderDisabled(provider: String) {
        Log.w(TAG, "GPS provider disabled: $provider")
    }
    
    // =========================================================================
    // IMU LISTENER
    // =========================================================================
    
    private fun registerImuListeners(): Boolean {
        var success = true
        
        if (accelerometer != null) {
            val registered = sensorManager.registerListener(
                this,
                accelerometer,
                SensorManager.SENSOR_DELAY_GAME  // ~50 Hz
            )
            if (!registered) {
                Log.e(TAG, "Failed to register accelerometer listener")
                success = false
            } else {
                Log.i(TAG, "Accelerometer listener registered")
            }
        } else {
            Log.e(TAG, "No accelerometer available")
            success = false
        }
        
        if (gyroscope != null) {
            val registered = sensorManager.registerListener(
                this,
                gyroscope,
                SensorManager.SENSOR_DELAY_GAME  // ~50 Hz
            )
            if (!registered) {
                Log.e(TAG, "Failed to register gyroscope listener")
                success = false
            } else {
                Log.i(TAG, "Gyroscope listener registered")
            }
        } else {
            Log.e(TAG, "No gyroscope available")
            success = false
        }
        
        return success
    }
    
    private fun unregisterImuListeners() {
        try {
            sensorManager.unregisterListener(this)
            Log.i(TAG, "IMU listeners unregistered")
        } catch (e: Exception) {
            Log.e(TAG, "Error unregistering IMU listeners: ${e.message}")
        }
    }
    
    override fun onSensorChanged(event: SensorEvent?) {
        if (state != RecordingState.RECORDING || event == null) return
        
        when (event.sensor.type) {
            Sensor.TYPE_ACCELEROMETER -> {
                lastAccelTimestampNs = event.timestamp
                lastAccelValues = event.values.clone()
            }
            Sensor.TYPE_GYROSCOPE -> {
                lastGyroTimestampNs = event.timestamp
                lastGyroValues = event.values.clone()
            }
        }
        
        // Combine when we have both (use most recent of each)
        val accel = lastAccelValues
        val gyro = lastGyroValues
        
        if (accel != null && gyro != null) {
            // Use the most recent timestamp
            val timestampNs = maxOf(lastAccelTimestampNs, lastGyroTimestampNs)
            
            // Convert nanoseconds since boot to Unix epoch milliseconds
            // event.timestamp is in nanoseconds since boot
            val timestampMs = convertSensorTimestampToEpochMs(timestampNs)
            
            // Check for IMU gaps
            if (lastImuTimestampMs > 0) {
                val gapMs = timestampMs - lastImuTimestampMs
                if (gapMs > 100) {  // > 100ms (expecting ~20ms at 50Hz)
                    imuGapWarningCount++
                    if (imuGapWarningCount <= 10) {  // Limit log spam
                        Log.w(TAG, "IMU gap detected: ${gapMs}ms (warning #$imuGapWarningCount)")
                    }
                }
            }
            lastImuTimestampMs = timestampMs
            
            val sample = IMUSample(
                timestamp_ms = timestampMs,
                accel_x_mps2 = accel[0],
                accel_y_mps2 = accel[1],
                accel_z_mps2 = accel[2],
                gyro_x_rps = gyro[0],
                gyro_y_rps = gyro[1],
                gyro_z_rps = gyro[2]
            )
            
            synchronized(imuSamples) {
                imuSamples.add(sample)
            }
            
            // Clear to avoid duplicates
            lastAccelValues = null
            lastGyroValues = null
        }
    }
    
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        Log.d(TAG, "Sensor accuracy changed: ${sensor?.name} -> $accuracy")
    }
    
    // =========================================================================
    // TIMESTAMP CONVERSION
    // =========================================================================
    
    /**
     * Convert sensor timestamp (nanoseconds since boot) to Unix epoch milliseconds.
     * 
     * CRITICAL: Android sensor timestamps are NOT Unix time.
     * They are nanoseconds since device boot (SystemClock.elapsedRealtimeNanos).
     * 
     * We compute the boot time once at startup and use it to convert.
     */
    private fun convertSensorTimestampToEpochMs(sensorTimestampNs: Long): Long {
        // sensorTimestampNs is nanoseconds since boot
        // bootTimeMillis is Unix epoch when device booted
        // Result: Unix epoch milliseconds
        return bootTimeMillis + (sensorTimestampNs / 1_000_000)
    }
    
    // =========================================================================
    // FILE OUTPUT
    // =========================================================================
    
    private fun writeSessionFile(): String? {
        try {
            // Build JSON
            val json = buildSessionJson()
            
            // Generate filename
            val dateFormat = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US)
            val filename = "session_${dateFormat.format(Date(startTimestampMs))}.json"
            
            // Write to app's external files directory
            val dir = getExternalFilesDir(null) ?: filesDir
            val file = File(dir, filename)
            
            file.writeText(json.toString(2))  // Pretty print with 2-space indent
            
            Log.i(TAG, "File written: ${file.absolutePath}")
            Log.i(TAG, "File size: ${file.length()} bytes")
            
            return filename
            
        } catch (e: Exception) {
            Log.e(TAG, "Failed to write session file: ${e.message}")
            e.printStackTrace()
            return null
        }
    }
    
    private fun buildSessionJson(): JSONObject {
        val json = JSONObject()
        
        // Header
        json.put("schema_version", "1.0")
        json.put("session_id", sessionId)
        json.put("start_timestamp_ms", startTimestampMs)
        json.put("end_timestamp_ms", endTimestampMs)
        json.put("device_model", android.os.Build.MODEL)
        json.put("os_version", "Android ${android.os.Build.VERSION.RELEASE}")
        json.put("app_version", "0.1.0")
        
        // Orientation
        val orientation = JSONObject()
        orientation.put("device_orientation", "UNKNOWN")  // Would need screen rotation
        orientation.put("gravity_vector", JSONArray(orientationGravityVector?.toList() ?: listOf(0, 0, -9.81)))
        json.put("orientation", orientation)
        
        // GPS samples
        val gpsArray = JSONArray()
        synchronized(gpsSamples) {
            for (sample in gpsSamples) {
                gpsArray.put(sample.toJson())
            }
        }
        json.put("gps_samples", gpsArray)
        
        // IMU samples
        val imuArray = JSONArray()
        synchronized(imuSamples) {
            for (sample in imuSamples) {
                imuArray.put(sample.toJson())
            }
        }
        json.put("imu_samples", imuArray)
        
        // Footer
        json.put("gps_sample_count", gpsSamples.size)
        json.put("imu_sample_count", imuSamples.size)
        json.put("duration_seconds", (endTimestampMs - startTimestampMs) / 1000.0)
        
        // Compute checksum of data portion
        val dataForChecksum = gpsArray.toString() + imuArray.toString()
        val checksum = sha256(dataForChecksum)
        json.put("checksum", "sha256:$checksum")
        
        return json
    }
    
    private fun sha256(input: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(input.toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
