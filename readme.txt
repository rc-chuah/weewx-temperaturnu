temperatur.nu - weewx extension that sends data to temperatur.nu

Copyright 2026 RC Chuah (Based on weewx-windy by Matthew Wall and Jacques Terrettaz)
Distributed under the terms of the GNU Public License (GPLv3)

You will need an API key from temperatur.nu

  https://www.temperatur.nu/nystation/

This extension will work with weewx version equal or greater than V3.8.0

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

Credits - Inspired by weewx-windy: https://github.com/Jterrettaz/weewx-windy
