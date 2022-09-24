from __future__ import annotations

import json
import logging
import os
from abc import abstractmethod
from collections import namedtuple
from collections import OrderedDict
from contextlib import AbstractContextManager
from datetime import datetime
import sentry_sdk


# initialize logging, TODO: use the helper logging library instead?
logging.basicConfig(level=logging.INFO)


# class JSONEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, OrderedDict):
#             return list(obj.items())


class pdf_logger:
    """Class for logging to console and structured json file"""

    log_entry = namedtuple('log_entry', ['name', 'message'])

    def __init__(self):
        self._history = []

    def log(self, name, message):
        # TODO: Use proper library for logging
        print(f'<{name}>:', message)
        self._history.append(pdf_logger.log_entry(name, message))

    @abstractmethod
    def to_json(self, slim=False):
        structure = OrderedDict()
        for entry in self._history:
            if entry.name in structure:
                structure[entry.name].append(entry.message)
            else:
                structure[entry.name] = [entry.message]

        if slim:
            slim_structure = dict()
            for key, values in structure.items():
                if len(values) == 1:
                    slim_structure[key] = values[0]
                else:
                    slim_structure[key] = values
            structure = slim_structure

        return json.dumps(structure, indent=4)

    def to_file(self, filename, slim=False, overwrite=False, *, force=False):
        # # fail safe solution to avoid overwriting files
        # if force and os.path.exists(filename):
        #     os.remove(filename)

        if overwrite:
            mode = 'w'
        else:
            mode = 'a'

        # Add a timestamp to each log entry
        with open(filename, mode) as file:
            # do not include a blank line at the beginning of the file
            if os.stat(filename).st_size != 0:
                file.write('\n')
            file.write(
                f'Log started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n',
            )
            file.write(self.to_json(slim=slim))


class PDF_Error(RuntimeError):
    """Superclass for special purpose exceptions types used by the pdf generator.

    An exception can be marked as critical. Non critical errors is ignored
    by the pdf_context context manager.
    """

    def __init__(self, value, critical=True):
        super().__init__(value)
        self.critical = critical


class BadData(PDF_Error):
    """Exception that documents some issue about input data

    Exceptions of this type is by default not critical.
    """

    def __init__(self, value, critical=False):
        super().__init__(value, critical=critical)


class pdf_context(AbstractContextManager):
    """Context manager for handling errors and logging

    If no error is caught and the execution exit the context normally,
    the string 'ok' is logged to the item_name provided in the constructor.

    If an error is caught, the exception name and description is logged. If the
    exception type is a subclass of PDF_Error and have member 'critical' set to False,
    then the exception will be silenced.
    """

    def __init__(self, logger, item_name):
        self._logger = logger
        self._item_name = item_name
        self._error = None

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        # print(error_type, error, traceback)
        caught_error = False

        if error is None:
            self._logger.log(self._item_name, 'ok')
        else:
            self._error = error

            self._logger.log(
                self._item_name,
                error_type.__name__ + ': ' + str(error),
            )

            if isinstance(error, PDF_Error):
                caught_error = (
                    not error.critical
                )  # Only catch non critical errors

        return caught_error


# test
# TODO: move to unit test module
logger = pdf_logger()

# send traces to sentry
sentry_sdk.init(
    dsn='https://013da30727a0486ba61fc38967f7874e@o1424581.ingest.sentry.io/6772723',
    traces_sample_rate = 1.0,
)

print('============ context manager test ============')
with pdf_context(logger, 'Page A') as ctx_A:
    pass

with pdf_context(logger, 'Page B') as ctx_B:
    raise BadData('Not enough data points')

with pdf_context(logger, 'Page C') as ctx_C:
    pass

# TODO: Handle visual things using the Error information in ctx?
for entry in logger._history:
    if ctx_A._error:
        print(f'Error in {ctx_A._item_name}: {ctx_A._error}')
        break
    if ctx_B._error:
        print(f'Error in {ctx_B._item_name}: {ctx_B._error}')
        break
    if ctx_C._error:
        print(f'Error in {ctx_C._item_name}: {ctx_C._error}')
        break


print('============ json dump test ============')
print('json_log.log')
print(logger.to_json(slim=False))
print('============ json slim test ============')
print(logger._history)
print('============ file handler test ============')
logger.to_file('json_log.log', slim=False, overwrite=False)
