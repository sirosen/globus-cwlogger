import time
from globus_cw_client.client import log_event, CWLoggerError


def time_failure(retries, wait):
    start = time.time()
    try:
        log_event("this log message should fail",
                  retries=retries, wait=wait)
    except CWLoggerError:
        pass
    finish = time.time()

    return finish - start


def main():
    print("fail_test.py")
    print("  confirm log_event takes its time retrying if we tell it to")
    time_taken = time_failure(retries=15, wait=0.1)
    assert(time_taken > 1.5)

    print("  confirm log_event fails quickly if we tell it to")
    time_taken = time_failure(retries=0, wait=0)
    assert(time_taken < 0.001)


if __name__ == "__main__":
    main()
