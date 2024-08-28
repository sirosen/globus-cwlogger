# globus-cwlogger

globus-cwlogger is a simple client and daemon for writing log data to
AWS CloudWatch Logs as an alternative to the AWS CloudWatch Agent.

Although globus-cwlogger is an open source project, it is not intended for
general use. We don't recommend that third parties depend upon it.

Requires Python 3.8+.

## Install, enable, and restart Daemon

```shell
sudo pip install git+https://github.com/globus/globus-cwlogger@1.0#subdirectory=daemon&egg=globus_cw_daemon
sudo globus_cw_daemon_install <group_name> --stream-name <optional_stream_name>
sudo systemctl -q enable globus_cw_daemon.service
sudo systemctl start globus_cw_daemon
```

## Install and use Client Module

```shell
pip install git+https://github.com/globus/globus-cwlogger@1.0#subdirectory=client&egg=globus_cw_client
```

```python
from globus_cw_client.client import log_event

log_event("some message string")

# logs with retries, for when the daemon is down or unreachable
# default is retries=10, wait=0.1
log_event("message which fails fast", retries=0, wait=0)
log_event("message which waits up to 60 seconds", retries=60, wait=1)
```

### Installation Without `subdirectory`

If you are using a non-pip tool to handle python packages, it may not support
`subdirectory`. In these cases, it's best to use the published sdist tarballs
for each release.

Daemon:

```shell
sudo pip3 install https://github.com/globus/globus-cwlogger/releases/download/1.0/daemon.tar.gz
```

Client:

```shell
pip install https://github.com/globus/globus-cwlogger/releases/download/1.0/client.tar.gz
```

### Using EMF Logs

globus-cwlogger supports use of the CloudWatch Embedded Metric Format.
For full details, see
link:https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html[the EMF specification].

Logging with EMF does not require any special options or considerations. For
example, this log will create a metric `foo` with a dimension
`bar='test-metric'`:

```python
import json
import time

from globus_cw_client.client import log_event


payload = {
    "foo": 1,
    "bar": "test-metric",
    "_aws": {
        "Timestamp": int(time.time()*1000),
        "CloudWatchMetrics": [
            {
                "Namespace": "globus-cwlogger-test",
                "Dimensions": [["bar"]],
                "Metrics": [{"Name": "foo", "Unit": "Count"}]
            }
        ]
    }
}
log_event(json.dumps(payload))
```
