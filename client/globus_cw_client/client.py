"""
Python client API for cwlogs daemon
"""

import json
import socket
import time


def _checktype(value, types, message):
    if not isinstance(value, types):
        raise TypeError(message)


def log_event(message, retries=10, wait=0.1):
    """
    Log the @message string to cloudwatch logs, using the current time.
    message: bytes (valid utf8 required) or unicode.
    retries: number of retries to make on failed socket connection
    wait: number of seconds to wait between retries
    Raises: exception if the message is too long or invalid utf8
    Raises: exception if the daemon is down or too backlogged
    Returns when the message was queued to the daemon's memory queue.
    (Does not mean the message is safe in cloudwatch)
    """
    # python3 json library can't handle bytes, so preemptively decode utf-8
    if isinstance(message, bytes):
        message = message.decode("utf-8")
    _checktype(message, str, "message type must be bytes or unicode")

    _checktype(retries, int, "retries must be an int")
    if retries < 0:
        raise ValueError("retries must be non-negative")

    _checktype(wait, (int, float), "wait must be an int or float")
    if wait < 0:
        raise ValueError("wait must be non-negative")

    req = {}
    req["message"] = message
    req["timestamp"] = int(time.time() * 1000)
    return _request(req, retries, wait)


def _connect(retries, wait):
    """
    Try to connect to the daemon @retries + 1 times,
    waiting @wait seconds between tries
    Raise: Exception if max attempts exceeded
    """
    addr = "\0org.globus.cwlogs"
    for _ in range(retries + 1):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        try:
            sock.connect(addr)
        except Exception as err:
            sock.close()
            error = err
        else:
            return sock
        time.sleep(wait)  # seconds

    raise CWLoggerConnectionError("couldn't connect to cw", error)


def _request(req, retries, wait):
    buf = json.dumps(req, indent=None) + "\n"
    # dumps returns unicode with python3, but sock requires bytes
    if isinstance(buf, str):
        buf = buf.encode("utf-8")

    sock = _connect(retries, wait)
    sock.sendall(buf)

    resp = ""
    while True:
        chunk = sock.recv(4000)
        if not chunk:
            raise Exception("no data")
        resp += chunk.decode("utf-8")
        if resp.endswith("\n"):
            break

    d = json.loads(resp[:-1])
    if isinstance(d, dict):
        status = d["status"]
        if status == "ok":
            return d
        else:
            raise CWLoggerDaemonError("forwarded error", d["message"])
    else:
        raise CWLoggerDaemonError("unknown response type", d)


"""
Ignore (swallow) these exceptions at your own risk.
CWLoggerDaemonError can be caused by many things, including but not limited to:
bad IAM policy, a killed / failed daemon background thread, AWS throttling,
invalid length/encoding.

Ignore only if you have some other mechanism
(e.g. a lambda / cloudwatch / heartbeat monitor) to ensure logs are properly configured
and working, and/or write logs to disk manually.

Note that even in the absence of exceptions, messages may still be lost - the daemon
has a very large memory queue and works asynchronously.
"""


class CWLoggerError(Exception):
    """
    Base class for exceptions raised by the CWLogger client.
    """


class CWLoggerConnectionError(CWLoggerError):
    """
    Raised when the CWLogger client is unable to talk
    to the daemon.
    """


class CWLoggerDaemonError(CWLoggerError):
    """
    Raised for errors returned to the client
    by the daemon.
    """
