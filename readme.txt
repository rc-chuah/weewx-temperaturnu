temperaturnu - weewx extension that sends data to temperatur.nu

Copyright 2026 RC Chuah (Based on weewx-windy by Matthew Wall and Jacques Terrettaz)
Distributed under the terms of the GNU Public License (GPLv3)

You will need an API key from temperatur.nu

  https://www.temperatur.nu/nystation/

This extension will work with weewx version equal or greater than V3.8.0

Requirements:

- Python 2.7+ or Python 3.x
- weewx V3.8.0 or later
- No external Python libraries required (uses only Python standard library)

Installation instructions:

1) download

wget -O weewx-temperaturnu.zip https://github.com/rc-chuah/weewx-temperaturnu/archive/master.zip

2) run the installer

wee_extension --install weewx-temperaturnu.zip     for weewx V4 and earlier

weectl extension install weewx-temperaturnu.zip    for weewx V5

3) enter parameters in the weewx configuration file

[StdRESTful]
    [[TemperaturNu]]
        apikey = YOUR_API_KEY_FROM_TEMPERATUR.NU

4) restart weewx

sudo systemctl restart weewx

Configuration:

The extension uses the following configuration parameters:

[StdRESTful]
    [[TemperaturNu]]
        # Your API key from temperatur.nu (required)
        apikey = YOUR_API_KEY_HERE
        
        # Optional: Enable or disable uploads (default: true)
        enabled = true
        
        # Optional: Server URL (default: https://www.temperatur.nu/rapportera.php)
        server_url = https://www.temperatur.nu/rapportera.php

The extension will:
- Monitor archive records from your weather station
- Extract the outdoor temperature (outTemp)
- Convert temperature to Celsius if your station uses Fahrenheit
- Upload to Temperatur.nu for each new archive record

Temperature Conversion:

The extension automatically detects your weather station's unit system and converts 
the temperature to Celsius as required by Temperatur.nu:

- If your station uses US units (Fahrenheit): (°F - 32) × 5/9 = °C
- If your station uses metric units (Celsius): No conversion needed
- Temperature is rounded to 1 decimal place

Example conversions:
- 32°F → 0°C
- 68°F → 20°C
- 72.5°F → 22.5°C
- 212°F → 100°C

Troubleshooting:

1) Check weewx logs for errors:
   tail -f /var/log/syslog | grep temperaturnu

2) Enable debug logging in weewx.conf:
   debug = 2

3) Test the extension manually:
   cd /usr/share/weewx
   PYTHONPATH=bin python bin/user/temperaturnu.py

4) Verify your API key is correct in weewx.conf

5) Ensure your weather station is recording temperature data (outTemp)

6) For connection issues, verify the URL is accessible:
   curl "https://www.temperatur.nu/rapportera.php?hash=YOUR_KEY&t=20"

Dependencies:

This extension uses only Python's standard library. The following standard library modules are used:

- Queue (or queue in Python 3)
- urllib (or urllib.parse and urllib.request in Python 3)
- sys
- time
- logging (or syslog)

No additional pip packages or external dependencies are required.

Credits - Inspired by weewx-windy: https://github.com/Jterrettaz/weewx-windy
