#!/bin/bash

# get a branch to test or default to master
if [ $# -eq 1 ]
then
    branch=$1
else
    # default to master
    branch="master"
fi

# cleanup any existing daemon or venv
sudo rm -f /etc/systemd/system/globus_cw_daemon.service
sudo rm -f /etc/cwlogd.ini
sudo pip uninstall globus_cw_daemon -y
rm -rf venv
set -e

# setup the daemon as root
sudo pip install git+https://github.com/globus/globus-cwlogger@$branch#subdirectory=daemon
sudo globus_cw_daemon_install cwlogger-test --stream-name test-stream
sudo systemctl daemon-reload
sudo service globus_cw_daemon restart
sudo service globus_cw_daemon status
