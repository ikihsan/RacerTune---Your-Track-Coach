# =============================================================================
# TRACK RECORDER V1 - VERIFICATION CHECKLIST
# =============================================================================
#
# Use this checklist to verify the sensor recorder works on a real device.
# Every check MUST pass before this slice is considered complete.
#
# =============================================================================

## PRE-FLIGHT CHECKS

### Environment
- [ ] Android Studio installed (2023.1+)
- [ ] Android SDK 34 installed
- [ ] USB debugging enabled on test device
- [ ] Device has GPS hardware
- [ ] Device has gyroscope and accelerometer

### Build
- [ ] Project opens in Android Studio without errors
- [ ] Gradle sync succeeds
- [ ] Build succeeds (no compile errors)
- [ ] APK installs on device

---

## PERMISSION CHECKS

### First Launch
- [ ] App requests location permission
- [ ] Permission dialog appears
- [ ] After granting, no crash occurs

### Permission Denied
- [ ] App does NOT crash if permission denied
- [ ] Status shows error message

---

## SENSOR ACTIVATION CHECKS

### GPS
- [ ] After START, GPS status shows "Active"
- [ ] GPS sample count increases
- [ ] GPS rate is ≥ 1 Hz (check: samples / duration)
- [ ] Logcat shows "GPS listener registered"

### IMU
- [ ] After START, IMU status shows "Active"
- [ ] IMU sample count increases rapidly
- [ ] IMU rate is ≥ 25 Hz (check: samples / duration)
- [ ] Logcat shows "Accelerometer listener registered"
- [ ] Logcat shows "Gyroscope listener registered"

---

## RECORDING CHECKS

### State Machine
- [ ] Initial state is IDLE
- [ ] START button changes state to RECORDING
- [ ] STOP button changes state to STOPPING, then IDLE
- [ ] Button text updates correctly

### Duration
- [ ] Duration counter increases while recording
- [ ] Duration is accurate (compare to wall clock)

### Sample Counts
- [ ] GPS count > 0 after outdoor recording
- [ ] IMU count >> GPS count (should be ~50x)

---

## FILE OUTPUT CHECKS

### File Creation
- [ ] File created after STOP
- [ ] Filename format: session_YYYYMMDD_HHMMSS.json
- [ ] File location: Android/data/com.f1.trackrecorder/files/
- [ ] File is not empty

### File Content - Header
- [ ] schema_version = "1.0"
- [ ] session_id is valid UUID
- [ ] start_timestamp_ms is reasonable Unix time
- [ ] end_timestamp_ms > start_timestamp_ms
- [ ] device_model matches test device
- [ ] os_version starts with "Android"
- [ ] app_version = "0.1.0"

### File Content - GPS Samples
- [ ] gps_samples is array
- [ ] Each sample has timestamp_ms
- [ ] Each sample has latitude_deg (valid range: -90 to 90)
- [ ] Each sample has longitude_deg (valid range: -180 to 180)
- [ ] Each sample has speed_mps (valid range: ≥ 0)
- [ ] Each sample has accuracy_m

### File Content - IMU Samples
- [ ] imu_samples is array
- [ ] Each sample has timestamp_ms
- [ ] Each sample has accel_x_mps2, accel_y_mps2, accel_z_mps2
- [ ] Each sample has gyro_x_rps, gyro_y_rps, gyro_z_rps
- [ ] At rest: accel magnitude ≈ 9.81 m/s²
- [ ] At rest: gyro values near zero (< 0.1 rad/s)

### File Content - Footer
- [ ] gps_sample_count matches gps_samples.length
- [ ] imu_sample_count matches imu_samples.length
- [ ] duration_seconds ≈ (end_timestamp_ms - start_timestamp_ms) / 1000
- [ ] checksum is present and starts with "sha256:"

---

## TIMESTAMP CHECKS (CRITICAL)

### Monotonicity
- [ ] GPS timestamps strictly increasing
- [ ] IMU timestamps strictly increasing

### Time Base Agreement
- [ ] GPS and IMU timestamps are in same epoch
- [ ] First GPS timestamp ≈ start_timestamp_ms (within 1s)
- [ ] Last GPS timestamp ≈ end_timestamp_ms (within 1s)

### Rate Verification
```
GPS rate = gps_sample_count / duration_seconds
Expected: ≥ 1 Hz

IMU rate = imu_sample_count / duration_seconds
Expected: ≥ 25 Hz
```

---

## STRESS CHECKS

### Long Recording (5+ minutes)
- [ ] App does not crash
- [ ] Memory usage stable (check Android Profiler)
- [ ] File saves successfully
- [ ] File size reasonable (estimate: ~1 MB per minute)

### Movement Test (walking/driving)
- [ ] GPS coordinates change
- [ ] GPS speed values > 0
- [ ] IMU shows acceleration changes
- [ ] No data corruption

---

## ERROR HANDLING CHECKS

### GPS Unavailable (indoors)
- [ ] App does not crash
- [ ] GPS sample count may be 0
- [ ] IMU still records
- [ ] File still saves

### App Backgrounded
- [ ] Recording stops (foreground-only)
- [ ] No crash on resume

---

## VALIDATION SCRIPT

Run this Python script on the output file:

```python
import json
import hashlib

def validate_session(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    errors = []
    
    # Schema version
    if data.get('schema_version') != '1.0':
        errors.append(f"Wrong schema: {data.get('schema_version')}")
    
    # Sample counts
    gps_count = len(data.get('gps_samples', []))
    imu_count = len(data.get('imu_samples', []))
    
    if data.get('gps_sample_count') != gps_count:
        errors.append(f"GPS count mismatch: {data.get('gps_sample_count')} vs {gps_count}")
    
    if data.get('imu_sample_count') != imu_count:
        errors.append(f"IMU count mismatch: {data.get('imu_sample_count')} vs {imu_count}")
    
    # Timestamp monotonicity
    gps_times = [s['timestamp_ms'] for s in data.get('gps_samples', [])]
    for i in range(1, len(gps_times)):
        if gps_times[i] <= gps_times[i-1]:
            errors.append(f"GPS timestamp not monotonic at index {i}")
            break
    
    imu_times = [s['timestamp_ms'] for s in data.get('imu_samples', [])]
    for i in range(1, len(imu_times)):
        if imu_times[i] <= imu_times[i-1]:
            errors.append(f"IMU timestamp not monotonic at index {i}")
            break
    
    # Duration check
    duration = data.get('duration_seconds', 0)
    expected_duration = (data['end_timestamp_ms'] - data['start_timestamp_ms']) / 1000
    if abs(duration - expected_duration) > 0.1:
        errors.append(f"Duration mismatch: {duration} vs {expected_duration}")
    
    # Rate checks
    if duration > 0:
        gps_rate = gps_count / duration
        imu_rate = imu_count / duration
        
        if gps_rate < 0.5:  # Allow some margin
            errors.append(f"GPS rate too low: {gps_rate:.2f} Hz")
        
        if imu_rate < 20:  # Allow some margin
            errors.append(f"IMU rate too low: {imu_rate:.2f} Hz")
    
    # Report
    print(f"File: {filepath}")
    print(f"GPS samples: {gps_count}")
    print(f"IMU samples: {imu_count}")
    print(f"Duration: {duration:.1f}s")
    
    if gps_count > 0 and duration > 0:
        print(f"GPS rate: {gps_count/duration:.2f} Hz")
    if imu_count > 0 and duration > 0:
        print(f"IMU rate: {imu_count/duration:.2f} Hz")
    
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("\n✓ All checks passed")
        return True

# Usage:
# validate_session('session_20260202_143022.json')
```

---

## SIGN-OFF

| Check | Date | Tester | Pass/Fail |
|-------|------|--------|-----------|
| Build succeeds | | | |
| Installs on device | | | |
| GPS records | | | |
| IMU records | | | |
| File saves | | | |
| Timestamps correct | | | |
| Validation script passes | | | |

---

## KNOWN LIMITATIONS (NOT BUGS)

1. **GPS may be 1 Hz**: Android LocationManager typically caps at 1 Hz even with minTime=0
2. **IMU rate varies**: SENSOR_DELAY_GAME is ~50 Hz but varies by device
3. **No background recording**: Foreground-only by design
4. **No satellite count**: Would require GnssStatus listener (added complexity)
5. **Orientation is approximate**: Gravity vector captured at start only

---

## NEXT STEPS (AFTER ALL CHECKS PASS)

1. Transfer session file to desktop
2. Run Python offline processor
3. Generate visualizations
4. Validate track shape matches reality
