"""
Install script for globus_cw_daemon, assumes being run on Ubuntu
Given a group_name as an argument
- Creates config file at at /etc/cwlogd.ini
- Copies globus_cw_daemon.service to /etc/systemd/system/
"""
import os
import shutil
import argparse
import ConfigParser as configparser


def main():

    install_dir_path = os.path.dirname(os.path.realpath(__file__))

    # get group name argument
    parser = argparse.ArgumentParser()
    parser.add_argument("group_name",
                        help="Name of the CloudWatch log group to log to.")
    args = parser.parse_args()
    group_name = args.group_name

    # read default-config.ini
    config = configparser.ConfigParser()
    config.read(install_dir_path + "/default-config.ini")

    # add group_name to config
    config.set("general", "group_name", group_name)

    # write config to /etc/cwlogd.ini
    config.write(open("/etc/cwlogd.ini", "w"))

    # globus_cw_daemon.service to /etc/systemd/system/
    shutil.copy(install_dir_path + "/globus_cw_daemon.service",
                "/etc/systemd/system/globus_cw_daemon.service")


if __name__ == "__main__":
    main()
