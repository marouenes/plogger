#!/usr/bin/env python3

from collections import OrderedDict, namedtuple
from contextlib import AbstractContextManager
import logging
import json


# initialize logging
logging.basicConfig(level=logging.INFO)

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, OrderedDict):
            return list(obj.items())


class pdf_logger(JSONEncoder):
    """ Class for logging to console and structured json file """
    log_entry = namedtuple('log_entry', ['name', 'message'])

    def __init__(self):
        self._history = []

    def log(self, name, message):
        # TODO: Use proper library for logging
        self.JSONEncoder = logging.StreamHandler(self._history)
        print(f'<{name}>:', message)
        self._history.append(pdf_logger.log_entry(name, message))

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


class PDF_Error(RuntimeError):
    """ Superclass for special purpose exceptions types used by the pdf generator.

    An exception can be marked as critical. Non critical errors is ignored
    by the pdf_context context manager.
    """
    def __init__(self, value, critical=True):
        super(PDF_Error, self).__init__(value)
        self.critical = critical


class BadData(PDF_Error):
    """ Exception that documents some issue about input data

    Exceptions of this type is by default not critical.
    """

    def __init__(self, value, critical=False):
        super(BadData, self).__init__(value, critical=critical)


class pdf_context(AbstractContextManager):
    """ Context manager for handling errors and logging

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
        #print(error_type, error, traceback)
        caught_error = False

        if error is None:
            self._logger.log(self._item_name, 'ok')
        else:
            self._error = error

            self._logger.log(self._item_name, error_type.__name__ + ': ' + str(error))


            if isinstance(error, PDF_Error):
                caught_error = not error.critical  # Only catch non critical errors

        return caught_error

# test
logger = pdf_logger()
with pdf_context(logger, 'Page A') as ctx_A:
    pass

with pdf_context(logger, 'Page B') as ctx_B:
    raise BadData('Not enough data points')

with pdf_context(logger, 'Page C') as ctx_C:
    pass

# TODO:
# Handle visual things using the Error information in ctx

print()
print('json log')
print(logger.to_json(slim=True))
print(logger._history)