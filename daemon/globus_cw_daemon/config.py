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
    """
    try:
        return _get_config().get("general", key)
    except configparser.NoOptionError:
        raise KeyError("key %s not found in %s" % (key, CONFIG_PATH))


def get_bool(key):
    """
    Given a key returns the value of that key in config as a boolean.
    A KeyError will be raised if no constant with the given key exists.
    A ValueError will be raised if the constant cannot be a boolean.
    """
    try:
        return _get_config().getboolean("general", key)
    except configparser.NoOptionError:
        raise KeyError("key %s not found in %s" % (key, CONFIG_PATH))


def get_int(key):
    """
    Given a key returns the value of that key in config as an int.
    A KeyError will be raised if no constant with the given key exists.
    A ValueError will be raised if the constant cannot be an int.
    """
    try:
        return _get_config().getint("general", key)
    except configparser.NoOptionError:
        raise KeyError("key %s not found in %s" % (key, CONFIG_PATH))
