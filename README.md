# Orange Pi with ESP32 TTGO TCall

![Workflow Status](https://github.com/muhammadhamidjamil/orangepi/workflows/Pylint/badge.svg)

In this repository, Python scripts are employed to automate a myriad of tasks, facilitating seamless communication with various interconnected projects. The codebase serves as a robust foundation for orchestrating and streamlining operations, promoting efficiency and coordination across multiple facets of the project ecosystem.

# Serial Interface Web App

This is a simple web application that allows you to view and interact with serial data from a device connected to your Orange Pi 5 Plus.

## Getting Started

1. **Install Dependencies:**
   Make sure you have Python, Flask, and PySerial installed.

   ```bash
   pip install Flask pyserial schedule requests beautifulsoup4 pyngrok python-dotenv pygame
   ```

2. **Run the App:**
   Open a terminal, navigate to the project directory, and run:

   ```bash
   python app.py
   ```

   Access the web interface at `http://127.0.0.1:6677` or `http://localhost:6677`. Replace the address with the IP of your Orange Pi for network access.

3. **Usage:**

   - The web page displays real-time serial data from the connected device.
   - Use the input field to send data back to the device.

4. **Customization:**
   - Modify the Python script (`app.py`) to adjust the serial port or customize the interface.
   - Update the HTML template (`templates/index.html`) to change the look and feel.

## Dependencies

- Python
- Flask
- PySerial
- see [discussions](https://github.com/mhamidjamil/orangePi/discussions/15) for more details

## License

This project is licensed under the [MIT License](LICENSE).

- How Orange Pi send commands to TTGO-TCall:
  {hay ttgo-tcall! here goes the query?}
- How TTGO_TCall send commands to Orange Pi:
  {hay orange-pi! here goes the query?}
Certainly! Here's a concise note for your README file:

New feature added to this project offers a streamlined solution for fetching upcoming Namaz (prayer) times and the current time, tailored for Lahore/Punjab, Pakistan. Additionally, it seamlessly integrates with the [TTGO TCall](https://github.com/mhamidjamil/TTGO_TCall) project, allowing users to leverage it as a Two-Factor Authentication (2FA) method.

**Key Features:**

- Retrieve Namaz Times for Lahore/Punjab, Pakistan.
- Obtain Current Time in the Local Time Zone.
- Integration with TTGO TCall for 2FA Verification.

**Usage:**

- To unlock the full potential of the 2FA feature, it is recommended to combine the functionalities of both the OrangePi and TTGO TCall projects.

Note:
Read me file might be out dated as I add almost 2 to 3 new features per week so do check closed issues to know which new feature is added.
