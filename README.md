# INSMART MEat Thermometer Custom Component for Home Assistant
Originally forked from https://github.com/jonwilliams84/ha-ble-scale

This custom component integrates the INSMART Meat Thermometer into Home Assistant, providing real-time termperature measurements.

## Features

- GUI based configuration
- Works with Bluetooth Proxies

## Installation

### HACS (Recommended)

1. Ensure that [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. In the HACS panel, click on the 3 dots in the top right corner.
3. Select "Custom repositories"
4. Add the URL "https://github.com/mukowman/ha-ble-insmart-thermometer" to the repository.
5. Select integration as the type.
6. Click the "ADD" button.

## Configuration

1. In Home Assistant, go to Configuration > Integrations.
2. Click the "+" button to add a new integration.
3. Search for "INSMART Thermometer" and select it.
4. Follow the configuration steps:
   - Select your BLE thermomenter from the list of discovered devices.
   - If your thermometer is not automatically discovered, you can manually enter its Bluetooth address.

## Usage

At the moment the only sensor support is the weight sensor which will return in grams.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Home Assistant community for their support and inspiration.
- Thanks to https://github.com/jonwilliams84 who I originally forked this repository from.
