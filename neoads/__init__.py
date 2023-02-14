import pkg_resources
from .core import (ElementDomain, CompositeString, CompositeArrayString, CompositeArrayNumber,
                   CompositeArrayDate, CompositeArrayObjectList, CompositeArrayObjectDict,
                   CompositeArrayObjectDataFrame, AbstractSet, AbstractMap, AbstractDLList)

from .simple import SimpleNumber, SimpleDate

from .exception import ObjectUnsavedError, ObjectDeletedError, ContainerNotEmpty, QueryNotExecuted, MemoryManagerError
from .memmanager import MemoryManager

__author__ = 'Athanasios Anastasiou'
__email__ = 'athanastasiou@gmail.com'
__license__ = 'MIT'
__package__ = 'neoads'
__version__ = pkg_resources.get_distribution('neoads').version
