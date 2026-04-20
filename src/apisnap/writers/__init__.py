"""Writers package for test output."""

from apisnap.writers.base_writer import BaseWriter
from apisnap.writers.pytest_writer import PytestWriter
from apisnap.writers.unittest_writer import UnittestWriter
from apisnap.writers.jest_writer import JestWriter
from apisnap.writers.mocha_writer import MochaWriter
from apisnap.writers.vitest_writer import VitestWriter
from apisnap.writers.restassured_writer import RestAssuredWriter
from apisnap.writers.rspec_writer import RSpecWriter
from apisnap.writers.httpx_writer import HttpxWriter

__all__ = [
    "BaseWriter",
    "PytestWriter",
    "UnittestWriter",
    "JestWriter",
    "MochaWriter",
    "VitestWriter",
    "RestAssuredWriter",
    "RSpecWriter",
    "HttpxWriter",
]

FORMAT_WRITERS = {
    "pytest": PytestWriter,
    "unittest": UnittestWriter,
    "jest": JestWriter,
    "mocha": MochaWriter,
    "vitest": VitestWriter,
    "restassured": RestAssuredWriter,
    "rspec": RSpecWriter,
    "httpx_test": HttpxWriter,
}


def get_writer(format: str) -> BaseWriter:
    """Get writer by format name."""
    return FORMAT_WRITERS.get(format, PytestWriter)()
