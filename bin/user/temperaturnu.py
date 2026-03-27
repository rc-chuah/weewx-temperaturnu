# Copyright 2026 RC Chuah (Based on weewx-windy by Matthew Wall and Jacques Terrettaz)

"""
This is a weewx extension that uploads data to temperatur.nu

https://www.temperatur.nu/

The protocol is described here:
https://www.temperatur.nu/rapportera.php

Minimal configuration:

[StdRESTful]
    [[TemperaturNu]]
        apikey = YOUR_API_KEY_HERE

"""

# deal with differences between python 2 and python 3
try:
    # noinspection PyCompatibility
    from Queue import Queue
except ImportError:
    # noinspection PyCompatibility
    from queue import Queue

try:
    from urllib import urlencode
except ImportError:
    # noinspection PyCompatibility
    from urllib.parse import urlencode

import sys
import time

import weewx
import weewx.manager
import weewx.restx
import weewx.units
from weeutil.weeutil import to_bool


VERSION = "0.1"


try:
    # Test for new-style weewx logging by trying to import weeutil.logger
    import weeutil.logger
    import logging

    log = logging.getLogger(__name__)


    def logdbg(msg):
        log.debug(msg)


    def loginf(msg):
        log.info(msg)


    def logerr(msg):
        log.error(msg)

except ImportError:
    # Old-style weewx logging
    import syslog


    def logmsg(level, msg):
        syslog.syslog(level, 'temperaturnu: %s' % msg)


    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)


    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)


    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)




class TemperaturNu(weewx.restx.StdRESTbase):
    DEFAULT_URL = 'https://www.temperatur.nu/rapportera.php'

    def __init__(self, engine, cfg_dict):
        super(TemperaturNu, self).__init__(engine, cfg_dict)
        loginf("version is %s" % VERSION)
        site_dict = weewx.restx.get_site_dict(cfg_dict, 'TemperaturNu', 'apikey')
        if site_dict is None:
            logerr("apikey is required for TemperaturNu")
            return
        site_dict.setdefault('server_url', TemperaturNu.DEFAULT_URL)

        binding = site_dict.pop('binding', 'wx_binding')
        mgr_dict = weewx.manager.get_manager_dict_from_config(
            cfg_dict, binding)

        self.archive_queue = Queue()
        self.archive_thread = TemperaturNuThread(self.archive_queue,
                                                  manager_dict=mgr_dict,
                                                  **site_dict)

        self.archive_thread.start()
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        loginf("Data will be uploaded to %s" % site_dict['server_url'])

    def new_archive_record(self, event):
        self.archive_queue.put(event.record)


class TemperaturNuThread(weewx.restx.RESTThread):

    def __init__(self, q, apikey, server_url=TemperaturNu.DEFAULT_URL,
                 skip_upload=False, manager_dict=None,
                 post_interval=None, max_backlog=sys.maxsize, stale=None,
                 log_success=True, log_failure=True,
                 timeout=60, max_tries=3, retry_wait=5):
        super(TemperaturNuThread, self).__init__(q,
                                                  protocol_name='TemperaturNu',
                                                  manager_dict=manager_dict,
                                                  post_interval=post_interval,
                                                  max_backlog=max_backlog,
                                                  stale=stale,
                                                  log_success=log_success,
                                                  log_failure=log_failure,
                                                  max_tries=max_tries,
                                                  timeout=timeout,
                                                  retry_wait=retry_wait)
        self.apikey = apikey
        self.server_url = server_url
        self.skip_upload = to_bool(skip_upload)

    def format_url(self, record):
        """Return a URL for doing a GET request to temperatur.nu
        
        Temperatur.nu expects temperature in Celsius.
        The format is: https://www.temperatur.nu/rapportera.php?hash=[APIKEY]&t=[TEMPERATURE IN °C]
        """
        url = self.server_url
        if weewx.debug >= 2:
            logdbg("url: %s" % url)
            
        # Convert record to metric units for temperature
        # Weewx internally stores data in a specific unit system
        # We need to get the temperature value and ensure it's in Celsius
        
        parts = dict()
        parts['hash'] = self.apikey
        
        # Try to get outTemp (outdoor temperature)
        # The record comes in the station's native units
        if 'outTemp' in record:
            temp_value = record['outTemp']
            
            # Get the unit system being used
            if 'usUnits' in record:
                unit_system = record['usUnits']
                # Convert to metric if necessary
                if unit_system == weewx.US:
                    # US units: temperature is in Fahrenheit
                    # Convert F to C: (F - 32) * 5/9
                    temp_celsius = (temp_value - 32.0) * 5.0 / 9.0
                elif unit_system == weewx.METRIC:
                    # Already in Celsius
                    temp_celsius = temp_value
                else:
                    # Assume METRICWX or other - try to convert
                    temp_celsius = temp_value
            else:
                # No unit system specified, assume it might be in Fahrenheit
                # Try to detect based on value range
                if temp_value > 50:
                    # Likely Fahrenheit
                    temp_celsius = (temp_value - 32.0) * 5.0 / 9.0
                else:
                    # Likely Celsius
                    temp_celsius = temp_value
            
            # Round to 1 decimal place for cleaner output
            parts['t'] = round(temp_celsius, 1)
            
            if weewx.debug >= 2:
                logdbg("Temperature raw: %s, converted to Celsius: %s" % (temp_value, parts['t']))
        else:
            logerr("No outTemp found in record")
            return None

        logdbg("%s?%s" % (url, urlencode(parts)))
        return "%s?%s" % (url, urlencode(parts))

    def process_record(self, record, manager):
        """Process the record and upload to Temperatur.nu"""
        try:
            url = self.format_url(record)
            if url is None:
                logerr("Failed to format URL for Temperatur.nu")
                return
            
            # Log the URL being sent (without the API key for security)
            safe_url = url.replace(self.apikey, "***")
            loginf("Posting to %s" % safe_url)
            
            # Use the parent class method to handle the actual HTTP request
            # This respects all the retry logic and error handling
            self.post_request(url, record, manager)
        except Exception as e:
            logerr("Error processing record: %s" % str(e))

    def post_request(self, url, record, manager):
        """Make the HTTP GET request to Temperatur.nu"""
        import requests
        
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                loginf("Successfully posted to Temperatur.nu")
            else:
                logerr("Temperatur.nu returned status code %d: %s" % (response.status_code, response.text))
        except Exception as e:
            logerr("Error posting to Temperatur.nu: %s" % str(e))


# Use this hook to test the uploader:
#   PYTHONPATH=bin python bin/user/temperaturnu.py

if __name__ == "__main__":
    class FakeMgr(object):
        table_name = 'fake'

        # noinspection PyUnusedLocal,PyMethodMayBeStatic
        def getSql(self, query, value):
            return None


    weewx.debug = 2
    queue = Queue()
    
    # Test with US units (Fahrenheit)
    t = TemperaturNuThread(queue, apikey='test_key_12345')
    r_us = {'dateTime': int(time.time() + 0.5),
            'usUnits': weewx.US,
            'outTemp': 72.5}  # 72.5°F ≈ 22.5°C
    
    print("Test 1 - US Units (Fahrenheit):")
    url_us = t.format_url(r_us)
    print(url_us)
    print()
    
    # Test with metric units (Celsius)
    r_metric = {'dateTime': int(time.time() + 0.5),
                'usUnits': weewx.METRIC,
                'outTemp': 22.5}  # 22.5°C
    
    print("Test 2 - Metric Units (Celsius):")
    url_metric = t.format_url(r_metric)
    print(url_metric)
