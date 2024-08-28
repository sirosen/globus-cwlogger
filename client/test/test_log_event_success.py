from globus_cw_client.client import log_event


def test_send_string_message(mock_socket):
    response = log_event("hello string world")
    assert response["status"] == "ok"


def test_send_bytes_message(mock_socket):
    response = log_event(b"hello bytes world")
    assert response["status"] == "ok"
