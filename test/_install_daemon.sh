#!/bin/bash -x

installpath="$1"

# cleanup any existing daemon or venv
sudo rm -f /etc/systemd/system/globus_cw_daemon.service
sudo rm -f /etc/cwlogd.ini
sudo -H pip uninstall globus_cw_daemon -y
sudo -H pip3 uninstall globus_cw_daemon -y
rm -rf venv

set -e

# setup the daemon as root
sudo -H pip3 install "$installpath"
sudo -H globus_cw_daemon_install cwlogger-test --stream-name "test-stream-$(uuidgen)"
sudo sed -i 's/local_log_level = info/local_log_level = debug/' /etc/cwlogd.ini
sudo systemctl daemon-reload
sudo service globus_cw_daemon restart
sudo service globus_cw_daemon status
