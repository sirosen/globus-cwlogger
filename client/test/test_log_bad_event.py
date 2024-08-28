import pytest

from globus_cw_client.client import log_event


@pytest.mark.parametrize("message", (object(), {"foo": "bar"}))
def test_log_event_rejects_bad_message_type(message):
    with pytest.raises(TypeError, match="must be bytes or unicode"):
        log_event(message)
