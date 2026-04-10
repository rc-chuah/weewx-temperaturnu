# weewx extension for temperaturnu
# Copyright © 2026 RC Chuah (Based on weewx-windy and weewx-temperaturnu by Matthew Wall, Jacques Terrettaz and Konrad Skeri Ekblad)
# Distributed under the terms of the GNU General Public License (GPLv3)

"""
This is a weewx extension that uploads data to temperatur.nu

https://www.temperatur.nu/

The protocol is described here:

https://www.temperatur.nu/info/rapportera-till-temperatur-nu/

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
        """Build the URL for GET request to temperatur.nu
        
        Temperatur.nu expects temperature in Celsius.
        The format is: https://www.temperatur.nu/rapportera.php?hash=[APIKEY]&t=[TEMPERATURE IN °C]
        """
        # Convert record to METRICWX (SI units) to get temperature in Celsius
        metric_record = weewx.units.to_METRICWX(record)
        
        # Build the query parameters
        parts = dict()
        parts['hash'] = self.apikey
        
        # Get temperature in Celsius
        if 'outTemp' in metric_record and metric_record['outTemp'] is not None:
            # Round to 1 decimal place
            parts['t'] = round(metric_record['outTemp'], 1)
            logdbg("Temperature converted to Celsius: %s" % parts['t'])
        else:
            logerr("No outTemp found in record")
            return None

        url = "%s?%s" % (self.server_url, urlencode(parts))
        logdbg("URL: %s?hash=***&t=%s" % (self.server_url, parts['t']))
        
        return url


# Use this hook to test the uploader:
# PYTHONPATH=bin python bin/user/temperaturnu.py

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
