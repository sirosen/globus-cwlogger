#!/usr/bin/python
"""
Upload messages to cloud watch logs
"""
import os, sys, socket, logging, time, errno, threading, json, traceback

import cwlogs
import config


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


def _script_exception_handler(fn):
    """
    If any Exception is raised by fn(),
    (excludes SystemExit and KeyboardInterrupt),
    log the error before raising.
    """
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            _log.error("script_exception_handler")
            _log.error(traceback.format_exc())
            raise
    return wrapper


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

    while True:
        time.sleep(FLUSH_WAIT_SECS)
        _log.info("checking queue")
        with _g_lock:
            new_data = _g_queue
            nr_dropped = _g_nr_dropped
            _g_queue = []
            _g_nr_dropped = 0

        _log.info("found %d events", len(new_data))
        if nr_dropped:
            _log.warn("dropped %d events", nr_dropped)
            event = _get_drop_event(nr_dropped)
            new_data.append(event)

        writer.upload_events(new_data)


def _get_drop_event(nr_dropped):
    data = dict(type="cwlogs.dropped", count=nr_dropped)
    ret = cwlogs.Event(timestamp=None, message=json.dumps(data))
    return ret


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
        response = dict(status="ok")
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


@_script_exception_handler
def main():

    root_logger = logging.getLogger()

    log_level = config.get_string("local_log_level")
    root_logger.setLevel(log_level.upper())

    # Change logging to use thread ids
    formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d %(levelname)s "\
                    "%(process)d:%(thread)d " + \
                    "%(name)s: %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S')

    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

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

    stream_name = os.uname()[1]  # hostname

    try:
        group_name = config.get_string("group_name")
    except KeyError:
        raise Exception("no group_name found in /etc/cwlogd.ini")

    writer = cwlogs.LogWriter(group_name, stream_name)

    flush_thread = threading.Thread(target=flush_thread_main, args=(writer,)) 
    flush_thread.daemon = True
    flush_thread.start()

    run_request_loop(listen_sock)


if __name__ == "__main__":
    main()
