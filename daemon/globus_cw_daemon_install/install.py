"""
Install script for globus_cw_daemon, assumes being run on Ubuntu ec2 instance
Given a group_name and an optional stream_name as arguments:
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
                        help="Name of the existing CloudWatch log group "
                        "to log to.")
    parser.add_argument("--stream_name",
                        help="Optional stream to override the daemon using "
                             "the current ec2 instance id.")
    args = parser.parse_args()
    group_name = args.group_name
    stream_name = args.stream_name

    # read default-config.ini
    config = configparser.ConfigParser()
    config.read(install_dir_path + "/default-config.ini")

    # add values to config
    config.set("general", "group_name", group_name)
    if stream_name:
        config.set("general", "stream_name", stream_name)

    # write config to /etc/cwlogd.ini
    config.write(open("/etc/cwlogd.ini", "w"))

    # globus_cw_daemon.service to /etc/systemd/system/
    shutil.copy(install_dir_path + "/globus_cw_daemon.service",
                "/etc/systemd/system/globus_cw_daemon.service")


if __name__ == "__main__":
    main()
