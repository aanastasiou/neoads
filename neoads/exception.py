"""
Exception hierarchy for neoads.

:author: Athanasios Anastasiou
:date: June 2018

"""


class NeoadsException(Exception):
    pass


class DataStructureError(NeoadsException):
    pass


class ObjectUnsavedError(DataStructureError):
    pass


class ObjectDeletedError(DataStructureError):
    pass


class ContainerNotEmpty(DataStructureError):
    """
    Raised when a container data type is about to be reset but it is not empty.
    """
    pass


class QueryNotExecuted(DataStructureError):
    """
    Raised when values from a query are requested but the query has not yet been executed.

    .. note::

        It is impossible to trigger an automatic query execution because queries have parameters which cannot be
        known or be passed to __getitem__ on the compositeAbstractObject.
    """
    pass


class MemoryManagerError(NeoadsException):
    """
    Raised when the memory manager encounters specific error conditions.
    """
    pass

class ObjectNotFound(MemoryManagerError):
    """
    Raised when a variable that does not exist is requested from the system.
    """
    pass
