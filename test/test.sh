# tests install and functionality of globus-cwlogger
# assumes run as a user with sudo access

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

# run client_test.py with python2
virtualenv venv
venv/bin/pip install git+https://github.com/globus/globus-cwlogger@$branch#subdirectory=client
venv/bin/python client_test.py
rm -rf venv

# run client_test.py with python3
virtualenv venv --python=python3
venv/bin/pip install git+https://github.com/globus/globus-cwlogger@$branch#subdirectory=client
venv/bin/python client_test.py
rm -rf venv

# stop the daemon and run fail_test.py
sudo service globus_cw_daemon stop

# with python2
virtualenv venv
venv/bin/pip install git+https://github.com/globus/globus-cwlogger#subdirectory=client
venv/bin/python fail_test.py
rm -rf venv

# with python3
virtualenv venv --python=python3
venv/bin/pip install git+https://github.com/globus/globus-cwlogger#subdirectory=client
venv/bin/python fail_test.py
rm -rf venv
