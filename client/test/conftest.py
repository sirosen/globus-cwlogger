import unittest.mock

import pytest


@pytest.fixture(autouse=True)
def mock_socket():
    mock_socket = unittest.mock.Mock()
    # this mock response matches a successful daemon response
    mock_socket.recv.return_value = (
        b'{"status":"ok","health":{"queue_length":0,"queue_percent_full":0}}\n'
    )
    mock_connect = unittest.mock.Mock(return_value=mock_socket)
    with unittest.mock.patch("globus_cw_client.client._connect", mock_connect):
        yield mock_socket
