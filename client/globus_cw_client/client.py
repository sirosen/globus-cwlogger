"""
Python client API for cwlogs daemon
"""
import time, socket, json

try:
    # Python 2
    UNICODE_TYPE = unicode
except NameError:
    # Python 3
    UNICODE_TYPE = str


def log_event(message):
    """
    Log the @message string to cloudwatch logs, using the current time.
    message: bytes (valid utf8 required) or unicode.
    Raises: exception if the message is too long or invalid utf8
    Raises: exception if the daemon is down or too backlogged
    Returns when the message was queued to the daemon's memory queue.
    (Does not mean the message is safe in cloudwatch)
    """
    # python3 json library can't handle bytes, so preemptively decode utf-8
    if isinstance(message, bytes):
        message = message.decode("utf-8")
    assert isinstance(message, UNICODE_TYPE)

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
    buf = json.dumps(req, indent=None) + "\n"
    # dumps returns unicode with python3, but sock requires bytes
    if isinstance(buf, UNICODE_TYPE):
        buf = buf.encode("utf-8")

    sock = _connect()
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
            raise Exception("forwarded error", d["message"])
    else:
        raise Exception("unknown response type", d)
