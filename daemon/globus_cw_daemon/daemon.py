#!/usr/bin/python
"""
Upload messages to cloud watch logs
"""
import os, sys, socket, logging, time, errno, threading, json

import globus_cw_daemon.cwlogs as cwlogs
import globus_cw_daemon.config as config


# Note that the total memory limit is double this:
# * the flush thread can be flushing MAX_EVENT_QUEUE_LEN
# * the front end thread can be receiving MAX_EVENT_QUEUE_LEN
MAX_EVENT_QUEUE_LEN = 100000

# The sucky thing about unix domain sockets.
# When this is full, clients will go into a retry sleep loop
SOCK_LISTEN_BACKLOG = 1024

# How long to sleep between successful queue flushes
FLUSH_WAIT_SECS = 1

_log = logging.getLogger(__name__)

# Data shared with flush thread
_g_lock = threading.Lock()
_g_queue = []   # List of Events
_g_nr_dropped = 0

# get constant instance_id on start
try:
    INSTANCE_ID = os.readlink("/var/lib/cloud/instance").split("/")[-1]
except OSError:
    INSTANCE_ID = None


def _print(m):
    sys.stdout.write(m + "\n")
    sys.stdout.flush()


def flush_thread_main(writer):
    try:
        _flush_thread_main(writer)
    except Exception as e:
        _log.exception(e)
        sys.exit(1)


def _flush_thread_main(writer):
    global _g_queue
    global _g_nr_dropped
    _log.info("flush_thread_main started")

    heartbeats = config.get_bool("heartbeats")
    hb_interval = config.get_int("heartbeat_interval")
    time_since_hb = 0

    while True:
        time.sleep(FLUSH_WAIT_SECS)
        if heartbeats:
            time_since_hb += FLUSH_WAIT_SECS
        _log.info("checking queue")

        with _g_lock:
            new_data = _g_queue
            nr_found = len(new_data)
            nr_dropped = _g_nr_dropped
            _g_queue = []
            _g_nr_dropped = 0

        _log.info("found %d events", nr_found)

        # if heartbeats are on and heartbeat_interval seconds have passed
        # then send a heartbeat to cw logs
        if heartbeats and time_since_hb >= hb_interval:
            hb_event = _get_heartbeat_event()
            new_data.append(hb_event)
            time_since_hb = 0

        if nr_dropped:
            _log.warn("dropped %d events", nr_dropped)
            event = _get_drop_event(nr_dropped)
            new_data.append(event)

        writer.upload_events(new_data)


def _get_drop_event(nr_dropped):
    data = dict(type="audit", subtype="cwlogs.dropped",
                dropped=nr_dropped, instance_id=INSTANCE_ID)
    ret = cwlogs.Event(timestamp=None, message=json.dumps(data))
    return ret


def _get_heartbeat_event():
    data = dict(type="audit", subtype="cwlogs.heartbeat",
                instance_id=INSTANCE_ID)
    ret = cwlogs.Event(timestamp=None, message=json.dumps(data))
    return ret


def _health_info():
    """
    compute daemon health info
    based only on the visible state of the frontend queue
    """
    q_len = len(_g_queue)  # no lock, but safe
    q_pct = q_len / float(MAX_EVENT_QUEUE_LEN)
    health_color = "green"
    if q_pct > 0.7:
        health_color = "red"
    elif q_pct > 0.5:
        health_color = "yellow"
    return dict(queue_length=q_len, queue_percent_full=q_pct,
                status=health_color)


def do_request(sock):
    """
    @sock: a client socket connection
    Post: response is sent but @sock is left open
    """
    # Read <json_data>\n
    buf = ""
    while True:
        chunk = sock.recv(4000)
        if not chunk:
            raise Exception("no data")
        buf += chunk
        if buf.endswith("\n"):
            break

    d = json.loads(buf[:-1])
    _log.debug("request: %r", d)

    try:
        _handle_request(d)
        response = dict(status="ok", health=_health_info())
    except Exception as e:
        _log.exception("error %r", e)
        response = dict(status="error", message=repr(e))

    _log.debug("response: %r", response)
    buf = json.dumps(response, indent=None) + "\n"
    sock.sendall(buf)


def _handle_request(d):
    event = cwlogs.Event(timestamp=d["timestamp"], message=d["message"])

    # do a local log if on debug level logging
    _log.debug("%s %s", event.timestamp, event.unicode_message)

    with _g_lock:
        if len(_g_queue) < MAX_EVENT_QUEUE_LEN:
            _g_queue.append(event)
        else:
            # For HIPAA, we prefer not to drop the record silently.
            # Send an error to the client.  We also record the drop count.
            # TODO: We could make this a special error code and clients
            # could sleep and retry a few times.  But we don't want to put a
            # sleep in this receiving thread, since that would stall other
            # requests indefinitely.
            global _g_nr_dropped
            _g_nr_dropped += 1
            raise Exception("too many events in queue")


def run_request_loop(listen_sock):
    while True:
        try:
            try:
                sock, addr = listen_sock.accept()
            except socket.error:
                continue
            try:
                _log.debug("accepted connection")
                do_request(sock)
            finally:
                sock.close()
        except Exception:
            # Should not happen often; we try to forward all exceptions
            # Should only happen if client dies during request
            _log.exception("unhandled in socket_thread_main!")


def main():

    # send local logs to stderr
    local_log_level = config.get_string("local_log_level").upper()
    logging.basicConfig(
        level=local_log_level, stream=sys.stderr, datefmt='%Y-%m-%d %H:%M:%S',
        fmt=("%(asctime)s.%(msecs)03d %(levelname)s %(process)d:%(thread)d "
             "%(name)s: %(message)s"))

    _print("cwlogs: starting...")
    _log.info("starting")

    listen_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
    addr = "\0org.globus.cwlogs"
    try:
        listen_sock.bind(addr)
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            _print("cwlogs: already running")
            return
        else:
            raise

    _print("cwlogs: started ok")
    listen_sock.listen(SOCK_LISTEN_BACKLOG)

    try:
        stream_name = config.get_string("stream_name")
    except KeyError:
        if not INSTANCE_ID:
            raise Exception(
                "no stream_name found in /etc/cwlogd.ini, and "
                "no ec2 instance_id found in /var/lib/cloud/instance")
        else:
            stream_name = INSTANCE_ID

    try:
        group_name = config.get_string("group_name")
    except KeyError:
        raise Exception("no group_name found in /etc/cwlogd.ini, have you "
                        "run globus_cw_daemon_install?")

    writer = cwlogs.LogWriter(group_name, stream_name)

    flush_thread = threading.Thread(target=flush_thread_main, args=(writer,))
    flush_thread.daemon = True
    flush_thread.start()

    run_request_loop(listen_sock)


if __name__ == "__main__":
    main()
