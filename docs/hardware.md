---
title: Hardware Setup
---

PawVision is designed to run on single board computers (SBCs) such as the Raspberry Pi. To enable physical interaction, you can connect a button and a motion sensor to your device.

## GPIO Configuration

GPIO pin assignments for the button and motion sensor can be changed in the `pawvision_settings.json` configuration file. Update the following fields to match your wiring:

- `button_pin`: GPIO pin number for the button
- `motion_sensor_pin`: GPIO pin number for the motion sensor
- `motion_sensor_enabled`: Set to `true` to enable motion sensor support

Refer to your board’s pinout diagram to select the correct GPIO numbers.

## Required Components

- **Single Board Computer** (e.g., Raspberry Pi)
- **Push Button** (momentary switch)
- **Motion Sensor** (PIR sensor, e.g., HC-SR501)
- **Jumper wires**
- **Breadboard** (optional, for prototyping)

## Wiring the Button

1. **Connect one leg of the button** to the designated GPIO pin (see your configuration, e.g., `button_pin`).
2. **Connect the other leg** to a ground (GND) pin on the SBC.
3. The software uses an internal pull-up resistor, so no external resistor is required.

**Example (Raspberry Pi):**
- Button leg 1 → GPIO17 (physical pin 11)
- Button leg 2 → GND (physical pin 6)

## Wiring the Motion Sensor

1. **Connect the VCC pin** of the PIR sensor to a 3.3V or 5V power pin (check your sensor’s requirements).
2. **Connect the GND pin** to a ground pin on the SBC.
3. **Connect the OUT pin** to the designated GPIO pin (e.g., `motion_sensor_pin`).

**Example (Raspberry Pi):**
- VCC → 5V (physical pin 2)
- GND → GND (physical pin 6)
- OUT → GPIO27 (physical pin 13)

## Supported Motion Sensors

PawVision supports standard PIR (Passive Infrared) motion sensors, such as the HC-SR501. These sensors detect movement by measuring changes in infrared radiation.


### mmWave Sensors

mmWave (millimeter wave) sensors are also supported for motion detection. These sensors use radio waves to detect movement and offer:

- Higher sensitivity and range
- Ability to detect motion through certain materials (e.g., plastic, glass)
- Less sensitivity to temperature changes and sunlight

To use an mmWave sensor:
- Choose a module with a digital output compatible with your SBC’s GPIO (e.g., IWR6843, RCWL-0516).
- Wire the digital output pin to the configured `motion_sensor_pin`, similar to a PIR sensor.
- Ensure the sensor’s voltage levels match your board’s GPIO requirements (use a level shifter or voltage divider if needed).

Most modules with a simple HIGH/LOW output will work out of the box. If your sensor requires special handling, you may need to adjust the configuration or code accordingly.

## Notes

- Double-check your wiring before powering on the SBC.
- Update your configuration file (`pawvision_settings.json`) with the correct GPIO pin numbers.
- For permanent installations, consider soldering connections or using reliable connectors.

### Safety Advice: Resistors and Voltage Protection

For most basic setups, no extra diodes or resistors are strictly required. However, for added safety and reliability:

- **Button:**
	- You may add a small resistor (330Ω–1kΩ) in series with the GPIO pin to limit current in case of accidental shorts.
	- Hardware debounce (capacitor + resistor) is optional; software debounce is already implemented.

- **Motion Sensor:**
	- If your PIR sensor operates at 5V and your SBC GPIO is 3.3V tolerant, add a voltage divider (two resistors) or a logic level shifter to protect the GPIO pin.
	- A small series resistor (330Ω–1kΩ) can also help protect the pin.

- **Diodes:**
	- Not required for basic button or PIR sensor wiring.
	- Use a diode only if you expect possible reverse voltage or inductive loads (not typical for these components).

**Summary:**
- For most users, no extra diodes or resistors are strictly required.
- Adding a small series resistor (330Ω–1kΩ) to each GPIO input is a good precaution.
- Use a voltage divider or level shifter if your sensor output is 5V and your board’s GPIO is 3.3V.
