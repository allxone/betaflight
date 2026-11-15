# Project Purpose

Support drone configuration using Gemini AI tools to improve my flight experience.

# Hardware

**Drone**: BetaFPV Air 65 racing with 5-in-1 FC purchased in November 2025 (`craft_name`: `AIR65 R`).
- **Flight Controller**: `BETAFPVG473` (Manufacturer ID: `BEFH`, MCU: `STM32G47X`, `mcu_id`: `0039001d3443500320393652`), no barometer (`baro_hardware = NONE`).
- **Firmware**: Betaflight `4.5.0` (May 16 2024, MSP API `1.46`, `config rev: 93dfc69`).
- **Motors / ESC**: `DSHOT300` protocol with bidirectional DShot enabled (`dshot_bidir = ON`), `12` motor poles (`motor_poles = 12`), reversed rotation / props-out (`yaw_motors_reversed = ON`). PID profiles configured for `1219S` (active) and `HQ 31mm` propellers.
- **Battery**: 1S LiHV configuration (`vbat_max_cell_voltage = 440` / 4.40V, `vbat_warning_cell_voltage = 345` / 3.45V), `ibata_offset = -600`.
- **Telemetry / Beacon**: `TELEMETRY` enabled, beacon on `RX_LOST` and `RX_SET`.

**Radio Transmitter**: Radiomaster Pocket ELRS

**Video Transmitter**: Integrated VTX on the 5-in-1 FC (controlled via Betaflight `vtxtable`).
- **Supported power levels**: `25`, `100`, `200`, `400` mW and `PIT` (`powervalues`: `1 2 3 4 0`).
- **Bands**: 6 bands × 8 channels (`BOSCAM_A`, `BOSCAM_B`, `BOSCAM_E`, `FATSHARK`, `RACEBAND`, `LOWRACE`).
- **Current configuration**: `RACEBAND` (band 5), channel `8` (`5917 MHz`), power `1` (`25 mW`).
- **OSD**: Enabled (`feature OSD`), video system `AUTO`, grid `30×13`.

**Goggles**: Skyzone Cobra X V4

**Batteries**: 10× LAVA 300mAh 1S LiHV 75C 3.8V 1.14Wh

**Charger**: VIFLY Whoopstor 3
