"""
Provides access to /etc/cwlogd.ini config values
"""
import ConfigParser as configparser

CONFIG_PATH = "/etc/cwlogd.ini"
_config = None


def _get_config():
    """
    Either returns an already loaded configparser
    Or creates a configparser and loads ini config at /etc/cwlogd.ini
    """
    global _config
    if _config is None:
        _config = configparser.ConfigParser()
        _config.read(CONFIG_PATH)

    return _config


def get_string(key):
    """
    Given a key returns the value of that key in config as a string.
    A KeyError will be raised if no constant with the given key exists.
    A ValueError will be raised if the constant cannot be a string.
    """
    try:
        value = _get_config().get("general", key)
        return str(value)
    except Exception:
        raise KeyError("key %s not found in %s" % (key, CONFIG_PATH))
