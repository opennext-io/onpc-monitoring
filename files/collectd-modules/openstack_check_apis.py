#!/usr/bin/python
# Copyright 2015 Mirantis, Inc.
# Copyright 2018, OpenNext SAS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Collectd plugin for checking the status of OpenStack API services

if __name__ == '__main__':
    import collectd_fake as collectd
else:
    import collectd

import collectd_openstack as openstack

from urlparse import urlparse

PLUGIN_NAME = 'openstack_check_apis'
INTERVAL = openstack.INTERVAL

class APICheckPlugin(openstack.CollectdPlugin):
    """Class to check the status of OpenStack API services."""

    states = {0: 'okay', 1: 'failed', 2: 'unknown'}

    # TODO(all): sahara, murano
    CHECK_MAP = {
        'keystone':
            {'path': '', 'expect': [300], 'name': 'keystone'},
        'heat':
            {'path': 'build_info', 'expect': [200], 'name': 'heat', 'auth': True},
        'heat-cfn':
            {'path': '/', 'expect': [300], 'name': 'heat-cfn'},
        'glance':
            {'path': '', 'expect': [300], 'name': 'glance'},
        'cinder':
            {'path': 'limits', 'expect': [200], 'name': 'cinder', 'auth': True},
        'cinderv2':
            {'path': 'limits', 'expect': [200], 'name': 'cinderv2', 'auth': True},
        'cinderv3':
            {'path': 'limits', 'expect': [200], 'name': 'cinderv3', 'auth': True},
        'neutron':
            {'path': '', 'expect': [200], 'name': 'neutron'},
        'nova':
            {'path': '', 'expect': [200], 'name': 'nova', 'auth': True},
        # Ceilometer requires authentication for all paths
        'ceilometer':
            { 'path': 'capabilities', 'expect': [200], 'name': 'telemetry', 'auth': True},
        'swift':
            {'path': 'healthcheck', 'expect': [200], 'name': 'swift'},
        'swift_s3':
            { 'path': 'healthcheck', 'expect': [200], 'name': 'swift-s3'},
        'placement':
            { 'path': '', 'expect': [200], 'name': 'placement', 'auth': True}
    }

    def __init__(self, *args, **kwargs):
        super(APICheckPlugin, self).__init__(*args, **kwargs)
        self.plugin = PLUGIN_NAME
        self.interval = INTERVAL
        self.timeout = 2
        self.max_retries = 1

    def compose_service_url(self, endpoint, path):
        u = urlparse(endpoint)
        # Dirty hack to handle the case of heat-cfn api
        if path == '/':
            url = '%s://%s' % (u.scheme, u.netloc)
        else:
            url = u.geturl()
            if len(path) != 0:
                url = '%s/%s' % (url, path)
        return url 

    def check_api(self):
        """ Check the status of all the API services.

            Yields a list of dict items with 'service', 'status' (either OK,
            FAIL or UNKNOWN) and 'region' keys.
        """
        catalog = self.service_catalog
        for service in catalog:
            name = service['name']
            
            if name not in self.CHECK_MAP:
                self.logger.notice(
                    "No check found for service '%s', skipping it" % name)
                status = self.UNKNOWN
                check = {}
            else:
                check = self.CHECK_MAP[name]
                url = self.compose_service_url(service['url'], check['path'])
                self.logger.info(
                    "Check status of service '%s' at '%s'" % (name, url))
                r = self.raw_get(url, token_required=check.get('auth', False))

                if r is None or r.status_code not in check['expect']:
                    def _status(ret):
                        return 'None' if r is None else r.status_code

                    self.logger.notice(
                        "Service %s check failed "
                        "(returned '%s' but expected '%s')" % (
                            name, _status(r), check['expect'])
                    )
                    status = self.FAIL
                else:
                    status = self.OK

            yield {
                'service': check.get('name', name),
                'status': status,
                'region': service['region']
            }

    def itermetrics(self):
        for item in self.check_api():
            # if item['status'] != self.UNKNOWN:
                # skip if status is UNKNOWN
                yield {
                    'plugin': PLUGIN_NAME,
                    'plugin_instance': item['service'],
                    'type_instance': self.states[item['status']],
                    'values': item['status'],
                    'meta': {
                        'region': item['region'],
                        'service': item['service'],
                        'discard_hostname': True,
                    },
                }


plugin = APICheckPlugin(collectd, PLUGIN_NAME, disable_check_metric=True)


def config_callback(conf):
    plugin.config_callback(conf)


def notification_callback(notification):
    plugin.notification_callback(notification)


def read_callback():
    plugin.conditional_read_callback()

if __name__ == '__main__':
    collectd.load_configuration(plugin)
    plugin.read_callback()
else:
    collectd.register_config(config_callback)
    collectd.register_notification(notification_callback)
    collectd.register_read(read_callback, INTERVAL)
