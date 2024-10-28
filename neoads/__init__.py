"""
Abstact Data Structures over neo4j.

:author: Athanasios Anastasiou
:date: Feb 2023
"""

from .simple import IntegerValue, FloatValue, DateValue
from .core import ValueReference, ValuePair


from .composite_array import (StringValue, ArrayOfString, ArrayOfInteger,
                              ArrayOfFloat, ArrayOfDate) 

from .query_interface import (ListQueryInterface, DictQueryInterface)

try:
    from .query_interface import DataframeQueryInterface
except ImportError:
    pass

# from .ads_abstractset import AbstractSet
# from .ads_abstractmap import AbstractMap
# from .ads_abstractdllist import AbstractDLList

# from .exception import ObjectUnsavedError, ObjectDeletedError, ContainerNotEmpty, QueryNotExecuted, MemoryManagerError
# from .memmanager import MemoryManager

__author__ = 'Athanasios Anastasiou'
__email__ = 'athanastasiou@gmail.com'
__license__ = 'MIT'
__package__ = 'neoads'
