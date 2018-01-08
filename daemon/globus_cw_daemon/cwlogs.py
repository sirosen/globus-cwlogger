"""
Upload logs to cloudwatch.
- log records too old are discarded by AWS (tooOldLogEventEndIndex)
- log records in the future are discarded by AWS (tooNewLogEventStartIndex)
"""
import os
import time
import logging

import boto


MAX_EVENT_BYTES = (256 * 1024)

# These make our batches conform to the AWS API
MAX_BATCH_BYTES = 800000            # Officially 1MB
MAX_BATCH_RECORDS = 5000            # Officially 10,000
MAX_BATCH_RANGE_HOURS = 6           # Officially 24 hours

_log = logging.getLogger(__name__)


class InvalidMessage(Exception): pass


class Event(object):
    def __init__(self, timestamp, message, enforce_limit=True):
        """
        Raise: InvalidMessage if message is too long
        Raise: UnicodeDecodeError if message is not valid utf8
        """
        if isinstance(message, str):
            message = message.decode("utf-8")
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        assert isinstance(timestamp, int)
        assert isinstance(message, unicode)
        assert timestamp >= 0
        encoded_message = message.encode("utf-8")
        self.timestamp = timestamp
        self.unicode_message = message
        self.size_in_bytes = len(encoded_message) + 26
        if self.size_in_bytes > MAX_EVENT_BYTES and enforce_limit:
            raise InvalidMessage("message too large")



class _Batch(object):
    def __init__(self):
        self.nr_bytes = 0
        self.records = []


    def add(self, record):
        """
        Return True if record was added to this batch, otherwise False
        Prereq: records are in timestamp order
        """
        assert isinstance(record, Event)

        if len(self.records) >= MAX_BATCH_RECORDS:
            return False

        if self.records:
            if self.time_diff_exceeded(self.records[0], record):
                return False

        if (self.nr_bytes + record.size_in_bytes) >= MAX_BATCH_BYTES:
            return False

        self.records.append(record)
        self.nr_bytes += record.size_in_bytes
        return True


    def get_records_for_boto(self):
        ret = []
        for r in self.records:
            ret.append(dict(timestamp=r.timestamp,
                message=r.unicode_message))
        return ret


    @staticmethod
    def time_diff_exceeded(a, b):
        diff_ms = b.timestamp - a.timestamp
        assert diff_ms >= 0
        return (diff_ms >= (3600 * MAX_BATCH_RANGE_HOURS * 1000))


class LogWriter(object):
    def __init__(self, group_name, stream_name):
        """
        Create the @stream_name if it doesn't exist.
        Raise: exception if boto can't connect.
        """
        _log.info("LogWriter init, %s, %s", group_name, stream_name)

        # Keep a connection around for performance.  boto is smart enough
        # to refresh role creds right before they expire (see provider.py).
        self.conn = boto.connect_logs()

        self.group_name = group_name
        self.stream_name = stream_name
        self.sequence_token = None

        try:
            self.conn.create_log_stream(self.group_name, self.stream_name)
        except boto.logs.exceptions.ResourceAlreadyExistsException:
            pass

        # It's easier just to pick up InvalidSequenceTokenException.
        # (Not documented by AWS, though)
        """
        streams = self.conn.describe_log_streams(group_name)
        for stream in streams["logStreams"]:
            stream_name = stream["logStreamName"]
            if stream_name == self.stream_name:
                # NB: Newly created streams dont have this attribute
                self.sequence_token = stream.get("uploadSequenceToken", None)
        """


    def upload_events(self, events):
        events = list(events)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        while events:
            batch = _Batch()
            while events:
                event = events[-1]
                if not batch.add(event):
                    break
                events.pop()

            _log.info("flushing batch, bytes=%d, recs=%d",
                    batch.nr_bytes, len(batch.records))
            self._flush_events(batch.get_records_for_boto())


    def _flush_events(self, events):
        """
        Upload a single batch of events.
        All exceptions are retried forever.
        """
        assert len(events)
        while True:
            try:
                ret = self.conn.put_log_events(self.group_name, 
                        self.stream_name, 
                        events, 
                        sequence_token=self.sequence_token)
                _log.info("flush ok")
                self.sequence_token = ret["nextSequenceToken"]
                #raise Exception("test")
                return
            except boto.logs.exceptions.DataAlreadyAcceptedException as e:
                _log.info("DataAlreadyAcceptedException")
                self.sequence_token = e.body["expectedSequenceToken"]
                return
            except boto.logs.exceptions.InvalidSequenceTokenException as e:
                _log.info("InvalidSequenceTokenException")
                self.sequence_token = e.body["expectedSequenceToken"]
            except Exception as e:
                _log.error("error: %r", e)
                time.sleep(3)


def test():
    logging.basicConfig()

    def now_ms():
        import time
        time.sleep(0.1)
        return int(time.time() * 1000)

    def hours(n):
        return 3600*n*1000

    writer = LogWriter("transfer-dev-tapi")

    events = []
    events.append(Event(now_ms(), "Test Event 1"))
    events.append(Event(now_ms() - hours(7), "Test Event 2"))
    events.append(Event(now_ms(), "Test Event 3"))
    writer.upload_events(events)

    events = []
    # These just fit
    events.append(Event(now_ms(), u"\n" * 262118))
    events.append(Event(now_ms(), u"\u00a9" * 131059))

    # Invalid utf8
    #events.append(Event(now_ms(), "\xff\xff"))

    # These are rejected by AWS
    #events.append(Event(now_ms(), u"\n" * 262119, enforce_limit=False))
    #events.append(Event(now_ms(), u"\u00a9" * 131060, enforce_limit=False))
    writer.upload_events(events)


if __name__ == "__main__":
    test()
