@echo off

python CombineHexFiles.py "C:\MyStuff\Nordic\nRF5 SDK\components\softdevice\s132\hex\s132_nrf52_4.0.2_softdevice.hex" "C:\MyStuff\Nordic\nRF5 SDK\examples\dfu\bootloader_secure_ble\pca10040_debug\arm5_no_packs\_build\nrf52832_xxaa_s132.hex" "C:\MyStuff\SureFi\Projects\SureFi-BLE-Bridge-Pairing\Objects\BLEBridgePairing.hex" "output.hex" > output.log