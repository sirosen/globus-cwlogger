# Globus CloudWatch Logger CHANGELOG

## Unreleased

## 1.2 - 2024-08-28

* Close instantiated sockets on connection error to prevent `ResourceWarning`s.

## 1.1 - 2021-06-08

* Drop client support for python2

## 1.1b1 - 2021-03-08

* add support for EMF-format logs

## 1.0 - 2019-08-02

* convert the daemon to python3-only -- the client is still py2/py3
* convert the daemon from boto to boto3
* apply black, isort, and flake8 as linting/code-quality checks and formatting
  standards
* tune several local INFO level log messages down to DEBUG to produce less
  noise in syslog
* local logging encodes priority levels for journald/syslog, can be handled via
  journald config as seen in daemon/globus_cw_daemon_install/example-journald.conf

## beta-4

* raise custom Exception classes in client
* add maintainers list
* fix Python3 Exception scope handling
* improve test suite with helpful print statements
* add queue fullness to heartbeats and client responses


## beta-3

* allow specifying client retry behavior
* lower default retry time to 10 retries at 0.1s each
* allow configuring daemon heartbeat behavior
* increase default time between heartbeats to 60s


## beta-2

* add audit daemon heartbeats on queue flushes
* update daemon dropped events to type audit


## beta-1

* first version
