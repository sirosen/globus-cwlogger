import sys

from globus_cw_client.client import log_event

try:
    # Python 2
    UNICODE_TYPE = unicode
except NameError:
    # Python 3
    UNICODE_TYPE = str


def main():
    print("client_test.py")

    print("  simple ascii test, confirms ascii str works for python2 and 3")
    log_event("Hello world from python%d!" % sys.version_info[0])

    print("  non ascii bytes test")
    byte_string = (
        b"Non-ascii utf-8 bytes: "
        b"\xe3\x83\x8f\xe3\x83\xad\xe3\x83\xbc\xe3\x83\xbb"
        b"\xe3\x83\xaf\xe3\x83\xbc\xe3\x83\xab\xe3\x83\x89"
    )
    assert isinstance(byte_string, bytes)
    log_event(byte_string)

    print("  non ascii unicode test")
    unicode_string = byte_string.decode("utf-8").replace("bytes", "unicode")
    assert isinstance(unicode_string, UNICODE_TYPE)
    log_event(unicode_string)


if __name__ == "__main__":
    main()
