"""
Python client API for cwlogs daemon
"""
import time
import socket
import json

try:
    # Python 2
    UNICODE_TYPE = unicode
except NameError:
    # Python 3
    UNICODE_TYPE = str


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
    assert isinstance(message, UNICODE_TYPE)

    assert(type(retries) == int)
    assert(retries >= 0)

    assert(type(wait) == int or type(wait) == float)
    assert(wait >= 0)

    req = dict()
    req["message"] = message
    req["timestamp"] = int(time.time() * 1000)
    _request(req, retries, wait)


def _connect(retries, wait):
    """
    Try to connect to the daemon @retries + 1 times,
    waiting @wait seconds between tries
    Raise: Exception if max attempts exceeded
    """
    addr = "\0org.globus.cwlogs"
    for i in range(retries+1):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        try:
            sock.connect(addr)
        except Exception as err:
            error = err
        else:
            return sock
        time.sleep(wait)  # seconds

    raise CWLoggerConnectionError("couldn't connect to cw", error)


def _request(req, retries, wait):
    buf = json.dumps(req, indent=None) + "\n"
    # dumps returns unicode with python3, but sock requires bytes
    if isinstance(buf, UNICODE_TYPE):
        buf = buf.encode("utf-8")

    sock = _connect(retries, wait)
    sock.sendall(buf)

    resp = u""
    while True:
        chunk = sock.recv(4000)
        if not chunk:
            raise Exception("no data")
        resp += chunk.decode("utf-8")
        if resp.endswith(u"\n"):
            break

    d = json.loads(resp[:-1])
    if isinstance(d, dict):
        status = d["status"]
        if status == "ok":
            return
        else:
            raise CWLoggerDaemonError("forwarded error", d["message"])
    else:
        raise CWLoggerDaemonError("unknown response type", d)


# Ignore (swallow) these exceptions at your own risk.
# CWLoggerDaemonError can be caused by many things, including but not limited to:
# bad IAM policy, a killed / failed daemon background thread, AWS throttling,
# invalid length/encoding.
# Ignore only if you have some other mechanism (e.g. a lambda / cloudwatch / heartbeat monitor)
# to ensure logs are properly configured and working, and/or write logs to disk manually.
# Note that even in the absence of exceptions, messages may still be lost - the daemon has a
# very large memory queue and works asynchronously.


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
