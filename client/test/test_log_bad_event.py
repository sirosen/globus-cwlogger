import pytest
from globus_cw_client.client import log_event


@pytest.mark.parametrize("message", (object(), {"foo": "bar"}))
def test_log_event_rejects_bad_message_type(message):
    with pytest.raises(TypeError, match="must be bytes or unicode"):
        log_event(message)


@pytest.mark.parametrize("retries", (object(), "100", 1.5))
def test_log_event_rejects_retries_type(retries):
    with pytest.raises(TypeError, match="retries must be an int"):
        log_event("hi", retries=retries)


def test_log_event_rejects_retries_value():
    with pytest.raises(ValueError, match="retries must be non-negative"):
        log_event("hi", retries=-5)


@pytest.mark.parametrize("wait", (object(), "100"))
def test_log_event_rejects_wait_type(wait):
    with pytest.raises(TypeError, match="wait must be an int or float"):
        log_event("hi", wait=wait)


def test_log_event_rejects_wait_value():
    with pytest.raises(ValueError, match="wait must be non-negative"):
        log_event("hi", wait=-1)
