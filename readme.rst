OpenNext Private Monitoring Stack
##################################
:date: 2018-01-13
:tags: openstack, ansible, opennext
:category: \*openstack, \*nix, \*monitoring

About this repository
---------------------

This set of playbooks will deploy Collectd, Telegraf, InfluxDB and Kapacitor
to collect metrics and monitor the healthiness of the OpenStack environment.

Process
-------

Before proceeding with the installation of the monitoring stack, you need to
setup the environment of an OpenNext deployment model.
Check the onpc-basic-model for a simple (a.k.a) "Starter Kit" deployment model.


Clone the onpc-monitoring repo

.. code-block:: bash

    cd /opt
    git clone https://github.com/opennext-io/onpc-monitoring.git
    cd /opt/onpc-monitoring

Create the monitoring container(s)

.. code-block:: bash

    openstack-ansible /opt/openstack-ansible/playbooks/lxc-containers-create.yml \
      -e container_group='influx_containers:collectd_containers:grafana_containers'

Create the monitoring user and install various python dependencies

.. code-block:: bash

    openstack-ansible playbook_setup.yml

If you are running HAProxy for load balacing you need run the following playbook as well to enable
the monitoring services backend and frontend.

.. code-block:: bash

    openstack-ansible playbook_haproxy.yml

If you already deployed OSA you also need to rerun the OSA HAProxy playbook
to enable the HAProxy stats.

.. code-block:: bash

    openstack-ansible /opt/openstack-ansible/playbooks/haproxy-install.yml


Install InfluxDB and InfluxDB Relay

.. code-block:: bash

    openstack-ansible playbook_influxdb.yml
    openstack-ansible playbook_influxdb_relay.yml

Install Telegraf

If you wish to install telegraf and point it at a specific target, or list of targets, set the ``telegraf_influxdb_targets``
variable in the ``user_onpc_variables.yml`` file as a list containing all targets that telegraf should send metrics to.

.. code-block:: bash

    openstack-ansible playbook_telegraf.yml --forks 50

Install Grafana

If you're proxy'ing grafana you will need to provide the full ``root_path``
when you run the playbook add the following ``-e grafana_url='https://cloud.something/grafana/'``

Note: Specifying the Grafana external URL won't work with http_proxy settings in the playbook.

.. code-block:: bash

    openstack-ansible playbook_grafana.yml

Once that last playbook is completed you will have a functioning InfluxDB, Telegraf, and Grafana metric collection system
active and collecting metrics. Grafana will need some setup, however functional dashboards have been provided in the
``grafana-dashboards`` directory.

Install Kapacitor (default all kapacitor targets)

.. code-block:: bash

   openstack-ansible playbook-kapacitor.yml -e 'kapacitor_host=<host target>' (optional)


OpenStack Swift PRoxy Server Dashboard
--------------------------------------

Once the telegraf daemon is installed onto each host, the Swift
proxy-server can be instructed to forward statsd metrics to telegraf.
The following configuration enabled the metric generation and need to
be added to the ``user_variables.yml``:

.. code-block:: yaml

    swift_proxy_server_conf_overrides:
      DEFAULT:
        log_statsd_default_sample_rate: 10
        log_statsd_metric_prefix: "{{ inventory_hostname }}.swift"
        log_statsd_host: localhost
        log_statsd_port: 8125


Rewrite the swift proxy server configuration with :

.. code-block:: bash

     cd /opt/openstack-ansible/playbooks
     openstack-ansible os-swift-setup.yml --tags swift-config --forks 2
