# -*- coding: utf-8 -*-
import os

from mkndaq.utils.configparser import config


def extract_recent_data(cfg, name=None, y=None, hours=6) -> object:
    """
    Select and import data files for a specified period into the past.

    :param int hours: numbers of hours to go back in time, defaults to 6
    :return:
    """
    try:
        if name is None:
            name = 'tei49i'

        if y is None:
            y = 'o3'

        # time stamp of earliest file to include
        earliest = int((datetime.datetime.utcnow() - datetime.timedelta(hours=6)).strftime("%Y%m%d%H%M"))

        # select data files
        files = os.listdir(os.path.expanduser(cls._datadir))
#            dtm = max(files).rstrip('.dat').split('-')[1]
#            ct = time.strptime(current_timestamp, "%Y%m%d%H%M")

        data = []
        for file in files:
            timestamp = int(file.rstrip('.dat').split('-')[1])
            if timestamp > earliest:
                # read file using pandas pd.read_csv
                # extract dtm and values of observed quantity y
                data.append([])
                # sort data by time ascending

        return data

    except Exception as err:
        print(err)
