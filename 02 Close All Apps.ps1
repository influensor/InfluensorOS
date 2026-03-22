$devices = adb devices | Select-String "device$" | ForEach-Object { ($_ -split '\s+')[0] }

foreach ($device in $devices) {
    Write-Output "Closing recent apps on device: $device"

    # Press Home button
    adb -s $device shell input keyevent KEYCODE_HOME
    Start-Sleep -Milliseconds 100  # Small delay

    # Open recent apps
    adb -s $device shell input keyevent KEYCODE_APP_SWITCH
    Start-Sleep -Milliseconds 100  # Small delay

    # Tap "Clear All" button at (350, 1450)
    adb -s $device shell input tap 350 1450
    Start-Sleep -Milliseconds 100  # Small delay
}

Write-Output "All apps cleared on all devices!"




$devices = adb devices | Select-String "device$" | ForEach-Object { ($_ -split '\s+')[0] }

foreach ($device in $devices) {
    Write-Output "Closing recent apps on device: $device"

    # Press Home button
    adb -s $device shell input keyevent KEYCODE_HOME
    Start-Sleep -Milliseconds 100  # Small delay

    # Open recent apps
    adb -s $device shell input keyevent KEYCODE_APP_SWITCH
    Start-Sleep -Milliseconds 100  # Small delay

    # Tap "Clear All" button at (350, 1450)
    adb -s $device shell input tap 350 1450
    Start-Sleep -Milliseconds 100  # Small delay
}

Write-Output "All apps cleared on all devices!"
