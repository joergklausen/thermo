import os
import shutil
import zipfile


def stage_file(self) -> None:
    """Stage a file if it is no longer written to. This is determined by checking if the path 
        of the file to be staged is different the path of the current (data)file.

    Raises:
        ValueError: _description_
        ValueError: _description_
        ValueError: _description_
    """
    try:
        if self.__datafile is None:
            raise ValueError("__datafile cannot be None.")
        if self.__staging is None:
            raise ValueError("__staging cannot be None.")
        if self.__datadir is None:
            raise ValueError("__datadir cannot be None.")

        if self.__file_to_stage is None:
            self.__file_to_stage = self.__datafile
        elif self.__file_to_stage != self.__datafile:
            root = os.path.join(self.__staging, os.path.basename(self.__datadir))
            os.makedirs(root, exist_ok=True)
            if self.__zip:
                # create zip file
                archive = os.path.join(root, "".join([os.path.basename(self.__file_to_stage)[:-4], ".zip"]))
                with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    zf.write(self.__file_to_stage, os.path.basename(self.__file_to_stage))
            else:
                shutil.copyfile(self.__file_to_stage, os.path.join(root, os.path.basename(self.__file_to_stage)))
            self.__file_to_stage = self.__datafile

    except Exception as err:
        if self._log:
            self._logger.error(err)
        print(err)


