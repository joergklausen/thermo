# -*- coding: utf-8 -*-

import os
import yaml


def expanduser_dict_recursive(d):
    try:
        for key, value in d.items():
            if isinstance(value, str):
                if '~' in value:
                    d[key] = os.path.expanduser(d[key])
            elif isinstance(value, dict):
                value = expanduser_dict_recursive(value)
    except Exception as err:
        print(err)

    finally:
        return d


def read_config(file) -> dict:
    """
    Read config file.

    :param file: full path to yaml config file
    :return: configuration information
    """
    try:
        print("# Read configuration from %s" % os.path.abspath(file))
        # print("# Read configuration from %s" % file)
        with open(os.path.abspath(file), "r") as fh:
        # with open(file, "r") as fh:
            cfg = yaml.safe_load(fh)
            fh.close()

        # see if HOME is set, otherwise set from config file
        try:
            if os.environ['HOME'] is None:
                os.environ['HOME'] = cfg['home']
        except Exception:
            os.environ['HOME'] = cfg['home']

        # expand all relative paths in config file
        cfg = expanduser_dict_recursive(cfg)

        return cfg

    except Exception as err:
        print(err)


if __name__ == "__main__":
    pass
