import unittest.mock

import pytest


@pytest.fixture(autouse=True)
def mock_socket():
    mock_socket = unittest.mock.Mock()
    mock_connect = unittest.mock.Mock(return_value=mock_socket)
    with unittest.mock.patch("globus_cw_client.client._connect", mock_connect):
        yield mock_socket
