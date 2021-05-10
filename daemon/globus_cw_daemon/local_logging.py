import logging
import logging.config

import globus_cw_daemon.config as config


class PrintKFormatter(logging.Formatter):
    """
    a formatter which encodes log levels in the way expected by syslog
    and journald -- adds the following prefixes for each level
      DEBUG:   "<7>"
      INFO:    "<6>"
      NOTICE : "<5>"
      WARNING: "<4>"
      ERR:     "<3>"
      CRIT:    "<2>"
      ALERT:   "<1>"
      EMERG:   "<0>"

    Note that these numeric values *don't* match the numeric values used by
    python for its log levels.

    This is called "PrintK" because this entire system of logging takes its
    inspiration from the printk() kernel logging facilities.
    """

    def __init__(self, *args, **kwargs):
        kwargs["fmt"] = (
            "%(asctime)s.%(msecs)03d %(levelname)s %(process)d:%(thread)d "
            "%(name)s: %(message)s"
        )
        kwargs["datefmt"] = "%Y-%m-%d %H:%M:%S"
        super().__init__(*args, **kwargs)

    def encode_level(self, record):
        # logging.handlers.SyslogHandler has an interesting note about
        # "INFO".lower() != "info" in certain locales...
        # so this is technically safer than `.lower()`, not that it's likely to
        # ever matter
        mapped_log_level = {
            "DEBUG": "debug",
            "INFO": "info",
            "WARNING": "warning",
            "ERROR": "error",
            "CRITICAL": "critical",
        }.get(record.levelname, "warning")

        return {"critical": 2, "error": 3, "warning": 4, "info": 6, "debug": 7}[
            mapped_log_level
        ]

    def format(self, record):
        level = f"<{self.encode_level(record)}>"
        return level + super().format(record)


def configure():
    """
    configure the globus_cw_daemon logger to write to stderr,

    Set up a stderr StreamHandler, PrintKFormatter, and log level pulled from
    config
    """
    logger = logging.getLogger("globus_cw_daemon")

    handler = logging.StreamHandler()
    formatter = PrintKFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    local_log_level = config.get_string("local_log_level").upper()
    logger.setLevel(local_log_level)
