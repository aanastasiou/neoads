import warnings
import os
import sys

from neomodel import config, db, clear_neo4j_database, change_neo4j_password


def pytest_sessionstart(session):
    """
    Provides initial connection to the database and sets up the rest of the test suite

    :param session: The session object. Please see <https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_sessionstart>`_
    :type Session object: For more information please see <https://docs.pytest.org/en/latest/reference.html#session>`_
    """

    warnings.simplefilter('default')

    if "NEO4J_BOLT_URL" in os.environ:
        config.DATABASE_URL = os.environ.get('NEO4J_BOLT_URL', 'bolt://neo4j:neo4j@localhost:7687')
    elif "NEO4J_USERNAME" in os.environ and "NEO4J_PASSWORD" in os.environ:
        config.DATABASE_URL = "bolt://{}:{}@localhost:7687".format(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    else:
        raise SystemError("Please set the authentication environment variables (either NEO4J_BOLT_URL or NEO4J_USERNAME and NEO4J_PASSWORD")
    config.AUTO_INSTALL_LABELS = True
