# -*- coding: utf-8 -*-
"""
Define a class TEI49I facilitating communication with a Thermo TEI49i instrument.

@author: joerg.klausen@meteoswiss.ch
"""

import logging
import os
import shutil
import socket
import re
import time
import zipfile

import colorama

import thermo.common.datetimebin as datetimebin


class TEI49I:
    """
    Instrument of type Thermo TEI 49I with methods, attributes for interaction.
    """

    _datadir = None
    __datafile = ""
    __data_header = None
    __get_config = None
    _get_data = None
    __id = None
    _log = None
    _logger = None
    __name = None
    _reporting_interval = None
    __set_config = None
    _simulate = None
    __sockaddr = None
    __socksleep = None
    __socktout = None
    _staging = None
    _zip = False

    def __init__(self, name: str, config: dict, simulate=False) -> None:
        """
        Initialize instrument class.

        :param name: name of instrument
        :param config: dictionary of attributes defining instrument, serial port and more
            - config[name]['type']
            - config[name]['id']
            - config[name]['serial_number']
            - config[name]['socket']['host']
            - config[name]['socket']['port']
            - config[name]['socket']['timeout']
            - config[name]['socket']['sleep']
            - config[name]['get_config']
            - config[name]['set_config']
            - config[name]['get_data']
            - config[name]['data_header']
            - config['logs']
            - config[name]['sampling_interval']
            - config['staging']['path'])
            - config[name]['staging_zip']
        :param simulate: default=True, simulate instrument behavior. Assumes a serial loopback connector.
        """
        colorama.init(autoreset=True)
        print(f"# Initialize TEI49I (name: {name})")

        try:
            self._simulate = simulate
            # setup logging
            if config['logs']:
                self._log = True
                logs = os.path.expanduser(config['logs'])
                os.makedirs(logs, exist_ok=True)
                logfile = f"{time.strftime('%Y%m%d')}.log"
                self._logger = logging.getLogger(__name__)
                logging.basicConfig(level=logging.DEBUG,
                                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                    datefmt='%y-%m-%d %H:%M:%S',
                                    filename=str(os.path.join(logs, logfile)),
                                    filemode='a')

            # read instrument control properties for later use
            self.__name = name
            self.__id = config[name]['id'] + 128
            self._type = config[name]['type']
            self._serial_number = config[name]['serial_number']
            self.__get_config = config[name]['get_config']
            self.__set_config = config[name]['set_config']
            self._get_data = config[name]['get_data']
            self.__data_header = config[name]['data_header']

            # configure tcp/ip
            self.__sockaddr = (config[name]['socket']['host'],
                             config[name]['socket']['port'])
            self.__socktout = config[name]['socket']['timeout']
            self.__socksleep = config[name]['socket']['sleep']

            # sampling, aggregation, reporting/storage
            self._sampling_interval = config[name]['sampling_interval']
            self._reporting_interval = config['reporting_interval']

            # setup data directory
            datadir = os.path.expanduser(config['data'])
            self._datadir = os.path.join(datadir, name)
            os.makedirs(self._datadir, exist_ok=True)

            # staging area for files to be transfered
            self._staging = os.path.expanduser(config['staging']['path'])
            self._zip = config[name]['staging_zip']

            # # query instrument to see if communication is possible, set date and time
            # if not self._simulate:
            #     dte = self.get_data('date', save=False)
            #     if dte:
            #         tme = self.get_data('time', save=False)
            #         msg = "Instrument '%s' initialized. Instrument datetime is %s %s." % (self.__name, dte, tme)
            #         self._logger.info(msg)
            #         self.set_datetime()
            #     else:
            #         msg = "Instrument '%s' did not respond as expected." % self.__name
            #         self._logger.error(msg)
            #     print(colorama.Fore.RED + "%s %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), msg))

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def tcpip_comm(self, cmd: str, tidy=True) -> str:
        """
        Send a command and retrieve the response. Assumes an open connection.

        :param cmd: command sent to instrument
        :param tidy: remove cmd echo, \n and *\r\x00 from result string, terminate with \n
        :return: response of instrument, decoded
        """
        __id = bytes([self.__id])
        rcvd = b''
        try:
            # open socket connection as a client
            if self._simulate:
                rcvd = self.simulate_get_data(cmd).encode()
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM, ) as s:
                    # connect to the server
                    s.settimeout(self.__socktout)
                    s.connect(self.__sockaddr)

                    if self._simulate:
                        __id = b''

                    # send data
                    s.sendall(__id + (f"{cmd}\x0D").encode())
                    time.sleep(self.__socksleep)

                    # receive response
                    while True:
                        data = s.recv(1024)
                        rcvd = rcvd + data
                        if b'\x0D' in data:
                            break

            # decode response, tidy
            rcvd = rcvd.decode()
            if tidy:
                # - remove checksum after and including the '*'
                rcvd = rcvd.split("*")[0]
                # - remove echo before and including '\n'
                rcvd = rcvd.replace(f"{cmd}\n", "")
                # if "\n" in rcvd:
                    # rcvd = rcvd.split("\n")[1]

            # TODO: test with local instrument
            # if rcvd is None:
            #     rcvd = ""

            return rcvd

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def get_config(self) -> list:
        """
        Read current configuration of instrument and optionally write to log.

        :return (err, cfg) configuration or errors, if any.

        """
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} .get_config (name={self.__name})")
        cfg = []
        try:
            for cmd in self.__get_config:
                cfg.append(self.tcpip_comm(cmd))

            if self._log:
                self._logger.info(f"Current configuration of '{self.__name}': {cfg}")

            return cfg

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def set_datetime(self) -> None:
        """
        Synchronize date and time of instrument with computer time.

        :return:
        """
        try:
            dte = self.tcpip_comm("set date %s" % time.strftime('%m-%d-%y'))
            msg = "Date of instrument %s set to: %s" % (self._name, dte)
            print("%s %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), msg))
            self._logger.info(msg)

            tme = self.tcpip_comm("set time %s" % time.strftime('%H:%M:%S'))
            msg = "Time of instrument %s set to: %s" % (self.__name, tme)
            print("%s %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), msg))
            self._logger.info(msg)

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def set_config(self) -> list:
        """
        Set configuration of instrument and optionally write to log.

        :return (err, cfg) configuration set or errors, if any.
        """
        print("%s .set_config (name=%s)" % (time.strftime('%Y-%m-%d %H:%M:%S'), self.__name))
        cfg = []
        try:
            for cmd in self.__set_config:
                cfg.append(self.tcpip_comm(cmd))
            time.sleep(1)

            if self._log:
                self._logger.info("Configuration of '%s' set to: %s" % (self.__name, cfg))

            return cfg

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def get_data(self, cmd=None, save=True) -> str:
        """
        Send command retrieve response from instrument and optionally write to log.

        :param str cmd: command sent to instrument
        :param bln save: Should data be saved to file? default=True
        :return str response as decoded string
        """
        try:
            dtm = time.strftime('%Y-%m-%d %H:%M:%S')
            if self._simulate:
                print("%s .get_data (name=%s, save=%s, simulate=%s)" % (dtm, self._name, save, self._simulate))
            else:
                print("%s .get_data (name=%s, save=%s)" % (dtm, self.__name, save))

            if cmd is None:
                cmd = self._get_data

            data = self.tcpip_comm(cmd)

            if self._simulate:
                data = self.simulate_get_data(cmd)

            if save:
                # generate the datafile name
                self.__datafile = os.path.join(self._datadir,
                                             "".join([self.__name, "-",
                                                      datetimebin.dtbin(self._reporting_interval), ".dat"]))

                if not os.path.exists(self.__datafile):
                    # if file doesn't exist, create and write header
                    with open(self.__datafile, "at", encoding='utf8') as fh:
                        fh.write(f"{self.__data_header}\n")
                        fh.close()
                with open(self.__datafile, "at", encoding='utf8') as fh:
                    fh.write(f"{dtm} {data}\n")
                    fh.close()

                # stage data for transfer
                root = os.path.join(self._staging, os.path.basename(self._datadir))
                os.makedirs(root, exist_ok=True)
                if self._zip:
                    # create zip file
                    archive = os.path.join(root, "".join([os.path.basename(self.__datafile[:-4]), ".zip"]))
                    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as fh:
                        fh.write(self.__datafile, os.path.basename(self.__datafile))
                else:
                    shutil.copyfile(self.__datafile, os.path.join(root, os.path.basename(self.__datafile)))

            return data

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def get_all_lrec(self, save=True) -> str:
        """download entire buffer from instrument and save to file

        :param bln save: Should data be saved to file? default=True
        :return str response as decoded string
        """
        try:
            dtm = time.strftime('%Y-%m-%d %H:%M:%S')

            # retrieve numbers of lrec stored in buffer
            no_of_lrec = self.tcpip_comm("no of lrec")
            no_of_lrec = int(re.findall(r"(\d+)", no_of_lrec)[0])

            if save:
                # generate the datafile name
                self.__datafile = os.path.join(self._datadir,
                                            "".join([self.__name, "_all_lrec-",
                                                    time.strftime("%Y%m%d%H%M%S"), ".dat"]))

            # retrieve all lrec records stored in buffer
            index = no_of_lrec
            retrieve = 10

            while index > 0:
                if index < 10:
                    retrieve = index
                cmd = f"lrec {str(index)} {str(retrieve)}"
                print(cmd)
                data = self.tcpip_comm(cmd)

                # remove all the extra info in the string returned
                # 05:26 07-19-22 flags 0C100400 o3 30.781 hio3 0.000 cellai 50927 cellbi 51732 bncht 29.9 lmpt 53.1 o3lt 0.0 flowa 0.435 flowb 0.000 pres 493.7
                data = data.replace("flags ", "")
                data = data.replace("hio3 ", "")
                data = data.replace("cellai ", "")
                data = data.replace("cellbi ", "")
                data = data.replace("bncht ", "")
                data = data.replace("lmpt ", "")
                data = data.replace("o3lt ", "")
                data = data.replace("flowa ", "")
                data = data.replace("flowb ", "")
                data = data.replace("pres ", "")
                data = data.replace("o3 ", "")

                if save:
                    if not os.path.exists(self.__datafile):
                        # if file doesn't exist, create and write header
                        with open(self.__datafile, "at", encoding='utf8') as fh:
                            fh.write("time date flags o3 hio3 cellai cellbi bncht lmpt o3lt flowa flowb pres\n")
                            fh.close()

                    with open(self.__datafile, "at", encoding='utf8') as fh:
                        fh.write(f"{data}\n")
                        fh.close()

                index = index - 10

            if save:
                # stage data for transfer
                root = os.path.join(self._staging, os.path.basename(self._datadir))
                os.makedirs(root, exist_ok=True)
                if self._zip:
                    # create zip file
                    archive = os.path.join(root, "".join([os.path.basename(self.__datafile[:-4]), ".zip"]))
                    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as fh:
                        fh.write(self.__datafile, os.path.basename(self.__datafile))
                else:
                    shutil.copyfile(self.__datafile, os.path.join(root, os.path.basename(self.__datafile)))

            return data

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def get_o3(self) -> str:
        try:
            return self.tcpip_comm('o3')

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def print_o3(self) -> None:
        try:
            o3 = self.tcpip_comm('O3').split()
            print(colorama.Fore.GREEN + "%s [%s] %s %s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"),
                                                        self.__name,
                                                        o3[0], str(float(o3[1])), o3[2]))

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def simulate_get_data(self, cmd=None) -> str:
        """

        :param cmd:
        :return:
        """
        if cmd is None:
            cmd = 'lrec'

        dtm = time.strftime("%H:%M %m-%d-%y", time.gmtime())

        if cmd == 'lrec':
            data = "(simulated) %s  flags D800500 o3 0.394 cellai 123853.000 cellbi 94558.000 bncht 31.220 lmpt " \
                   "53.754 o3lt 68.363 flowa 0.000 flowb 0.000 pres 724.798" % dtm
        else:
            data = "(simulated) %s Sorry, I can only simulate lrec. " % dtm

        return data


if __name__ == "__main__":
    pass
