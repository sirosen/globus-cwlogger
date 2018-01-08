# tests install and functionality of globus-cwlogger
# assumes run as a user with sudo access

#!/bin/bash

# cleanup any existing daemon or venv
sudo rm -f /etc/systemd/system/globus_cw_daemon.service
sudo rm -f /etc/cwlogd.ini
sudo pip uninstall globus_cw_daemon -y
rm -rf venv
set -e

# setup the daemon as root
sudo pip install git+https://github.com/globus/globus-cwlogger#subdirectory=daemon
sudo globus_cw_daemon_install cwlogger-test --stream_name test-stream
sudo systemctl daemon-reload
sudo service globus_cw_daemon restart
sudo service globus_cw_daemon status

# python 2 client test in venv
virtualenv venv
venv/bin/pip install git+https://github.com/globus/globus-cwlogger#subdirectory=client
venv/bin/python client_test.py
rm -rf venv

# python 3 client test in venv
virtualenv venv --python=python3
venv/bin/pip install git+https://github.com/globus/globus-cwlogger#subdirectory=client
venv/bin/python client_test.py
rm -rf venv
