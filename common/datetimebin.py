# -*- coding: utf-8 -*-

from datetime import datetime, timezone
from time import time


def dtbin(interval=10) -> str:
    """
    Generate a binned datetime string as suffix for datafiles.

    :param interval: minutes
                How often should a new file be generated? Values allowed are
                10, 15, 20, 30, 60, 120, 180, 240, 360, 720, 1440
    :return:
    """
    try:
        if interval in [10, 15, 20, 30, 60, 120, 180, 240, 360, 720, 1440]:
            t = time()
            interval *= 60
            nt = (t // interval) * interval + interval
            return datetime.fromtimestamp(nt, timezone.utc).strftime("%Y%m%d%H%M")
        else:
            raise ValueError("Interval must be in [10, 15, 20, 30, 60, 120, 180, 240, 360, 720, 1440]")
    except Exception as err:
        print(err)


if __name__ == "__main__":
    print(datetime.utcnow())
    print(dtbin(23))
    print(dtbin(10))
    print(dtbin(15))
    print(dtbin(20))
    print(dtbin(30))
    print(dtbin(360))
    print(dtbin(1440))
