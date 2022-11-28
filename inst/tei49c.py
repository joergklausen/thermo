# -*- coding: utf-8 -*-
"""
Class TEI49C facilitating communication with a Thermo TEI49c instrument.

@author: joerg.klausen@meteoswiss.ch
"""

# from datetime import datetime
import logging
import os
import shutil
import time
import zipfile
import serial

from mkndaq.utils import datetimebin


class TEI49C:
    """
    Instrument of type Thermo TEI 49C with methods, attributes for interaction.
    """

    _datadir = None
    _datafile = None
    _file_to_stage = None
    _data_header = None
    _get_config = None
    _get_data = None
    _id = None
    _log = False
    _logger = None
    _name = None
    _reporting_interval = None
    _serial = None
    _set_config = None
    _staging = None
    _zip = False

    def __init__(self, name: str, config: dict) -> None:
        """
        Initialize instrument class.

        :param name: name of instrument
        :param config: dictionary of attributes defining the instrument, serial port and other information
            - config['id']
            - config[name]['port']
            - config[port]['baudrate']
            - config[port]['bytesize']
            - config[port]['parity']
            - config[port]['stopbits']
            - config[port]['timeout']
            - config[name]['data_header']
            - config[name]['type']
            - config[name]['serial_number']
        :param simulate: default=True, simulate instrument behavior. Assumes a serial loopback connector.
        """
        print(f"# Initialize {name}")

        try:
            # instrument identification
            self._name = name
            self._id = config[name]['id'] + 128
            self._type = config[name]['type']
            self._serial_number = config[name]['serial_number']

            # serial communication settings
            port = config[name]['port']
            self._serial = serial.Serial(port=port,
                                        baudrate=config[port]['baudrate'],
                                        bytesize=config[port]['bytesize'],
                                        parity=config[port]['parity'],
                                        stopbits=config[port]['stopbits'],
                                        timeout=config[port]['timeout'])
            if self._serial.is_open:
                self._serial.close()

            # instrument configuration
            self._get_config = config[name]['get_config']
            self._set_config = config[name]['set_config']

            # sampling, aggregation, reporting/storage
            self._sampling_interval = config[name]['sampling_interval']
            self._reporting_interval = config['reporting_interval']

            # data file header and command to get data
            self._get_data = config[name]['get_data']
            self._data_header = config[name]['data_header']

            # setup data directory and staging area
            self._datadir = os.path.join(os.path.expanduser(config['data']), name)
            os.makedirs(self._datadir, exist_ok=True)
            self._staging = os.path.expanduser(config['staging']['path'])
            self._zip = config[name]['staging_zip']

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

            # # query instrument to see if communication is possible, set date and time
            # if not self._simulate:
            #     dte = self.get_data('date', save=False)
            #     if dte:
            #         tme = self.get_data('time', save=False)
            #         msg = "Instrument '%s' initialized. Instrument datetime is %s %s." % (self._name, dte, tme)
            #         self._logger.info(msg)
            #
            #         # set date and time
            #         self.set_datetime()
            #     else:
            #         msg = "Instrument '%s' did not respond as expected." % self._name
            #         self._logger.error(msg)
            #     print(colorama.Fore.RED + "%s %s" % (time.strftime('%Y-%m-%d %H:%M:%S'), msg))

        # except serial.SerialException as err:
        #     if self._log:
        #         self._logger.error(err)
        #     print(err)

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def serial_comm(self, cmd: str, tidy=True) -> str:
        """
        Send a command and retrieve the response. Assumes an open connection.

        :param cmd: command sent to instrument
        :param tidy: remove echo and checksum after '*'
        :return: response of instrument, decoded
        """
        _id = bytes([self._id])
        rcvd = b''
        try:
            if self._simulate:
                _id = b''
            self._serial.write(_id + (f"{cmd}\x0D").encode())
            time.sleep(0.5)
            while self._serial.in_waiting > 0:
                rcvd = rcvd + self._serial.read(1024)
                time.sleep(0.1)

            rcvd = rcvd.decode()
            if tidy:
                # - remove checksum after and including the '*'
                rcvd = rcvd.split("*")[0]
                # - remove echo before and including '\n'
                if cmd.join("\n") in rcvd:
                    rcvd = rcvd.split("\n")[1]
                # remove trailing '\r\n'
                rcvd = rcvd.rstrip()
            return rcvd

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def get_config(self) -> list:
        """
        Read current configuration of instrument and optionally write to log.

        :return current configuration of instrument

        """
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} .get_config (name={self._name})")
        cfg = []
        try:
            self._serial.open()
            for cmd in self._get_config:
                cfg.append(self.serial_comm(cmd))
            self._serial.close()

            if self._log:
                self._logger.info(f"Current configuration of '{self._name}': {cfg}")

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
            dte = self.serial_comm(f"set date {time.strftime('%m-%d-%y')}")
            dte = self.serial_comm("date")
            msg = f"Date of instrument {self._name} set and reported as: {dte}"
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}")
            self._logger.info(msg)

            tme = self.serial_comm(f"set time {time.strftime('%H:%M')}")
            tme = self.serial_comm("time")
            msg = f"Time of instrument {self._name} set and reported as: {tme}"
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}")
            self._logger.info(msg)

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


    def set_config(self) -> list:
        """
        Set configuration of instrument and optionally write to log.

        :return new configuration as returned from instrument
        """
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} .set_config (name={self._name})")
        cfg = []
        try:
            self._serial.open()
            self.set_datetime()
            for cmd in self._set_config:
                cfg.append(self.serial_comm(cmd))
            self._serial.close()
            time.sleep(1)

            if self._log:
                self._logger.info(f"Configuration of '{self._name}' set to: {cfg}")

            return cfg

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)

    
    def get_data(self, cmd=None, save=True) -> str:
        """
        Retrieve long record from instrument and optionally write to log.

        :param str cmd: command sent to instrument
        :param bln save: Should data be saved to file? default=True
        :return str response as decoded string
        """
        try:
            dtm = time.strftime('%Y-%m-%d %H:%M:%S')
            if self._simulate:
                print(f"{dtm} .get_data (name={self._name}, save={save}, simulate={self._simulate})")
            else:
                print(f"{dtm} .get_data (name={self._name}, save={save})")

            if cmd is None:
                cmd = self._get_data

            if self._simulate:
                data = self.simulate_get_data(cmd)
            else:
                if self._serial.is_open:
                    self._serial.close()

                self._serial.open()
                data = self.serial_comm(cmd)
                self._serial.close()

            if save:
                # generate the datafile name
                self._datafile = os.path.join(self._datadir,
                                             "".join([self._name, "-",
                                                      datetimebin.dtbin(self._reporting_interval), ".dat"]))

                if not os.path.exists(self._datafile):
                    # if file doesn't exist, create and write header
                    with open(self._datafile, "at", encoding='utf8') as fh:
                        fh.write(f"{self._data_header}\n")
                        fh.close()

                with open(self._datafile, "at", encoding='utf8') as fh:
                    # add data to file
                    fh.write(f"{dtm} {data}\n")
                    fh.close()

                # stage data for transfer
                if self._file_to_stage is None:
                    self._file_to_stage = self._datafile
                elif self._file_to_stage != self._datafile:
                    root = os.path.join(self._staging, os.path.basename(self._datadir))
                    os.makedirs(root, exist_ok=True)
                    if self._zip:
                        # create zip file
                        archive = os.path.join(root, "".join([os.path.basename(self._file_to_stage)[:-4], ".zip"]))
                        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                            zf.write(self._file_to_stage, os.path.basename(self._file_to_stage))
                    else:
                        shutil.copyfile(self._file_to_stage, os.path.join(root, os.path.basename(self._file_to_stage)))
                    self._file_to_stage = self._datafile

            return data

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)

    @classmethod
    def get_o3(self) -> str:
        try:
            self._serial.open()
            o3 = self.serial_comm('O3')
            self._serial.close()
            return o3

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)

    @classmethod
    def print_o3(self) -> None:
        try:
            self._serial.open()
            o3 = self.serial_comm('O3').split()
            self._serial.close()

            print(colorama.Fore.GREEN + f"{time.strftime('%Y-%m-%d %H:%M:%S')} [{self._name}] {o3[0]} {str(float(o3[1]))} {o3[2]}")

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)

    @classmethod
    def simulate_get_data(self, cmd=None) -> str:
        """

        :param cmd:
        :return:
        """
        if cmd is None:
            cmd = 'lrec'

        dtm = time.strftime("%H:%M %m-%d-%y", time.gmtime())

        if cmd == 'lrec':
            data = f"(simulated) {dtm}  flags D800500 o3 0.394 cellai 123853.000 cellbi 94558.000 bncht 31.220 lmpt " \
                   "53.754 o3lt 68.363 flowa 0.000 flowb 0.000 pres 724.798"
        else:
            data = f"(simulated) {dtm} Sorry, I can only simulate lrec. "

        return data

    @classmethod
    def get_all_rec(self, save=True) -> str:
        """
        Retrieve all long and short records from instrument and optionally write to file.

        :param bln save: Should data be saved to file? default=True
        :return str response as decoded string
        """
        try:
            dtm = time.strftime('%Y-%m-%d %H:%M:%S')

            # lrec and srec capacity of logger
            CMD = ["lrec", "srec"]
            CAPACITY = [1792, 4096]

            print("%s .get_all_rec (name=%s, save=%s)" % (dtm, self._name, save))

            # close potentially open port
            if self._serial.is_open:
                self._serial.close()

            # open serial port
            self._serial.open()

            # retrieve data from instrument
            for i in [0, 1]:
                index = CAPACITY[i]
                retrieve = 10
                if save:
                    # generate the datafile name
                    datafile = os.path.join(self._datadir,
                                            "".join([self._name, f"_all_{CMD[i]}-",
                                                    time.strftime("%Y%m%d%H%M00"), ".dat"]))

                while index > 0:
                    if index < 10:
                        retrieve = index
                    cmd = f"{CMD[i]} {str(index)} {str(retrieve)}"
                    print(cmd)
                    data = self.serial_comm(cmd)

                    if save:
                        if not os.path.exists(datafile):
                            # if file doesn't exist, create and write header
                            with open(datafile, "at") as fh:
                                fh.write(f"{self._data_header}\n")
                                fh.close()
                        with open(datafile, "at") as fh:
                            # add data to file
                            fh.write(f"{data}\n")
                            fh.close()

                    index = index - 10

                # stage data for transfer
                root = os.path.join(self._staging, os.path.basename(self._datadir))
                os.makedirs(root, exist_ok=True)
                if self._zip:
                    # create zip file
                    archive = os.path.join(root, "".join([os.path.basename(datafile[:-4]), ".zip"]))
                    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as fh:
                        fh.write(self._datafile, os.path.basename(datafile))
                else:
                    shutil.copyfile(self._datafile, os.path.join(root, os.path.basename(datafile)))

            self._serial.close()
            return 0

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)


if __name__ == "__main__":
    pass
