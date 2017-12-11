"""
Python client API for cwlogs daemon
"""
import time, socket, simplejson

import pykoa


def log_event(message):
    """
    Log the @message string to cloudwatch logs, using the current time.
    message: str (valid utf8 required) or unicode.
    Raises: exception if the message is too long or invalid utf8
    Raises: exception if the daemon is down or too backlogged
    Returns when the message was queued to the daemon's memory queue.
    (Does not mean the message is safe in cloudwatch)
    """
    assert isinstance(message, basestring)
    req = dict()
    req["message"] = message
    req["timestamp"] = int(time.time() * 1000)
    _request(req)


def _connect():
    """
    Try to connect to the daemon 
    Raise: Exception if max attempts exceeded
    """
    addr = "\0org.globus.cwlogs"
    for i in range(60):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        try:
            sock.connect(addr)
        except Exception:
            pass
        else:
            return sock
        time.sleep(0.5)  # seconds

    raise Exception("couldn't connect to cw")


def _request(req):
    if pykoa.isdebug():
        pykoa.debug("_request %r", req)

    buf = simplejson.dumps(req, indent=None) + "\n"
    sock = _connect()
    sock.sendall(buf)

    resp = ""
    while True:
        chunk = sock.recv(4000)
        if not chunk:
            raise Exception("no data")
        resp += chunk
        if resp.endswith("\n"):
            break

    d = simplejson.loads(resp[:-1])
    if isinstance(d, dict):
        status = d["status"]
        if status == "ok":
            return
        else:
            raise Exception("forwarded error", d["message"])
    else:
        raise Exception("unknown response type", d)


def _test():
    log_event("hello there dude")
    log_event("bad bytes \xff\x00\x01")
    #for i in xrange(300000):
        #log_event("load event %d" % i)
    #log_event(12345)  # forwards an assertion exception
    #log_event("h"*300000)  # forwards InvalidMessage


if __name__ == "__main__":
    _test()
