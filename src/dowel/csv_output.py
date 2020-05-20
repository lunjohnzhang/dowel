"""A `dowel.logger.LogOutput` for CSV files."""
import os
import csv
import warnings

from dowel import TabularInput
from dowel.simple_outputs import FileOutput
from dowel.utils import colorize


class CsvOutput(FileOutput):
    """CSV file output for logger.

    :param file_name: The file this output should log to.
    """

    def __init__(self, file_name):
        super().__init__(file_name)
        self._writer = None
        self._fieldnames = None
        self._warned_once = set()
        self._disable_warnings = False

    @property
    def types_accepted(self):
        """Accept TabularInput objects only."""
        return (TabularInput, )

    def _init_log_writer(self, mode, fieldnames, writeheader = True):
        """Initialize csv writer to log file using specified fieldnames,
        and update relevant values.
        """
        self._fieldnames = fieldnames
        self.mode = mode # mode may be upated to 'a'
        self._log_file, self._writer = self._init_writer(
            self._log_file.name,
            self.mode,
            self._fieldnames,
            writeheader)

    def _init_writer(self, filename, mode, fieldnames, writeheader = True):
        """Helper function to initialize a writer to a specified file"""
        f = open(filename, mode)
        writer = csv.DictWriter(f, fieldnames)
        if writeheader:
            writer.writeheader()
        return f, writer

    def record(self, data, prefix=''):
        """Log tabular data to CSV."""
        if isinstance(data, TabularInput):
            to_csv = data.as_primitive_dict
            new_fields = set(to_csv.keys())

            if not to_csv.keys() and not self._writer:
                return

            if not self._writer:
                self._init_log_writer(
                    mode = self.mode,
                    fieldnames = new_fields)

            # new fieldnames detected, need to read in current file, modify, and write everything again
            if to_csv.keys() != self._fieldnames:
                # close original log file
                self._log_file.close()

                # reader of original data
                origin_reader = csv.DictReader(open(self._log_file.name, 'r'))

                # writer of a tmp file
                tmp_file, tmp_file_writer = self._init_writer(
                    "tmp.csv", 'w',
                    new_fields)

                # read in original data line by line and write modified data to tmp file
                for row in origin_reader:
                    tmp_file_writer.writerow(row) # exploit restval variable to fill in empty entries

                # rename the file to log_file and reopen it
                tmp_file.close() # flush tmp file data
                os.rename("tmp.csv", self._log_file.name)
                self._init_log_writer(
                    fieldnames = new_fields,
                    mode='a',
                    writeheader=False)

            self._writer.writerow(to_csv)

            for k in to_csv.keys():
                data.mark(k)
        else:
            raise ValueError('Unacceptable type.')

    def disable_warnings(self):
        """Disable logger warnings for testing."""
        self._disable_warnings = True


class CsvOutputWarning(UserWarning):
    """Warning class for CsvOutput."""

    pass
