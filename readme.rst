OpenNext Private Cloud Monitoring Stack
#######################################
:date: 2018-01-13
:tags: openstack, ansible, monitoring
:category: \*openstack, \*nix


About this repository
---------------------

This set of playbooks will deploy InfluxDB, Telegraf, Grafana and Kapacitor for
the purpose of monitoring an OpenStack environment.

Process
-------

Clone the ONPC Monitoring repo

.. code-block:: bash

    cd /opt
    git clone git@github.com:opennext-io/onpc-monitoring.git

Copy the env.d files and global configuration variables into place

.. code-block:: bash

    cd /opt/onpc-monitoring
    cp ./etc/env.d/* /etc/openstack_deploy/env.d/
    cp ./etc/conf.d/* /etc/openstack_deploy/conf.d/
    cp ./etc/user_monitoring.yml /etc/openstack_deploy

Copy the secrets file into place and generate the password values

.. code-block:: bash

    cd /opt/onpc-monitoring
    cp user_monitoring_secrets.yml /etc/openstack_deploy/
    sudo /opt/openstack-ansible/scripts/pw-token-gen.py --file /etc/openstack_deploy/user_monitoring_secrets.yml

Import the ansible roles

.. code-block:: bash
    
    cd /opt/openstack-ansible/tests
    openstack-ansible get-ansible-role-requirements.yml -i ./test-inventory.ini \
        -e role_file=/opt/onpc-monitoring/ansible-role-requirements.yml -vvv


Add the export to update the inventory file location

.. code-block:: bash

    export ANSIBLE_INVENTORY=/opt/openstack-ansible/playbooks/inventory/dynamic_inventory.py

If you are running the HA Proxy you should run the following playbook as well to enable
the grafana port 8089

.. code-block:: bash

    openstack-ansible /opt/openstack-ansible/playbooks/playbook-metrics-lb.yml

Create the containers

.. code-block:: bash

    oopenstack-ansible /opt/openstack-ansible/playbooks/lxc-containers-create.yml -e container_group=monitoring_container

Install InfluxDB

.. code-block:: bash

    openstack-ansible /opt/openstack-ansible/playbooks/playbook-influx-db.yml

Install Influx Telegraf

If you wish to install telegraf and point it at a specific target, or list of targets, set the ``influx_telegraf_targets``
variable in the ``user_variables.yml`` file as a list containing all targets that telegraf should ship metrics to.

.. code-block:: bash

    openstack-ansible playbook-influx-telegraf.yml --forks 100

Install grafana

If you're proxy'ing grafana you will need to provide the full ``root_path`` when you run the playbook add the following
``-e grafana_root_url='https://cloud.something:8443/grafana/'``

.. code-block:: bash

    openstack-ansible playbook-grafana.yml -e galera_root_user=root -e galera_address='127.0.0.1'

Once that last playbook is completed you will have a functioning InfluxDB, Telegraf, and Grafana metric collection system
active and collecting metrics. Grafana will need some setup, however functional dashboards have been provided in the
``grafana-dashboards`` directory.

Install Kapacitor

.. code-block:: bash

   openstack-ansible playbook-kapacitor.yml


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
