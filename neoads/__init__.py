"""
Abstact Data Structures over neo4j.

:author: Athanasios Anastasiou
:date: Feb 2023
"""

import pkg_resources
from .core import ElementDomain

from .simple import SimpleNumber, SimpleDate

from .composite_array import (CompositeString, CompositeArrayString, CompositeArrayNumber,
                              CompositeArrayDate) 

from .composite_array_object import (CompositeArrayObjectList, CompositeArrayObjectDict)

try:
    from .composite_array_object import CompositeArrayObjectDataFrame
except ImportError:
    pass

from .ads import (AbstractSet, AbstractMap, AbstractDLList)

from .exception import ObjectUnsavedError, ObjectDeletedError, ContainerNotEmpty, QueryNotExecuted, MemoryManagerError
from .memmanager import MemoryManager

__author__ = 'Athanasios Anastasiou'
__email__ = 'athanastasiou@gmail.com'
__license__ = 'MIT'
__package__ = 'neoads'
__version__ = pkg_resources.get_distribution('neoads').version
