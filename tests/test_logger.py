# unit test module for pdf logger
# pylint: disable=missing-docstring,invalid-name
# pylint: disable=too-few-public-methods

import logger
import tempfile
import os

import pytest


# fixture for creating temporary directory for testing
@pytest.fixture
def temp_dir():
    """ Context manager for creating temporary directory """
    with tempfile.TemporaryDirectory() as temp_dir:
        return temp_dir  # yield instead?


def test_pdf_logger(temp_dir: str) -> None:
    """ test pdf logger """
    logger.pdf_logger()
    with logger.pdf_context(logger.pdf_logger(), 'Page A') as ctx_A:
        assert ctx_A is not None

    with logger.pdf_context(logger.pdf_logger(), 'Page B') as ctx_B:
        # raise logger.BadData('Not enough data points') # pylint: disable=no-member
        # exit context with error
        assert ctx_B is not None

    # check log file
    log_file = os.path.join(temp_dir, 'log.txt')
    with open(log_file, 'r') as f:
        lines = f.readlines()
        assert lines[0] == 'Page A: ok\n'
        assert lines[1] == 'Page B: BadData: Not enough data points\n'
