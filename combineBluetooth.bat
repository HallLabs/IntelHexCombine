@echo off

python CombineHexFiles.py "C:\MyStuff\Nordic\nRF5 SDK\components\softdevice\s132\hex\s132_nrf52_4.0.2_softdevice.hex" "C:\MyStuff\SureFi\Projects\NordicSecureDFU\Objects\NordicSecureDFU.hex" "C:\MyStuff\SureFi\Projects\SureFi-BLE-Bridge-Pairing\Objects\BLEBridgePairing.hex" "BluetoothHexCombined.hex" > output.log