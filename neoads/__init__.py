import pkg_resources
from .core import ElementDomain

from .simple import SimpleNumber, SimpleDate

from .composite_array import (CompositeString, CompositeArrayString, CompositeArrayNumber,
                              CompositeArrayDate, CompositeArrayObjectList, 
                              CompositeArrayObjectDict, CompositeArrayObjectDataFrame) 

from .ads import (AbstractSet, AbstractMap, AbstractDLList)

from .exception import ObjectUnsavedError, ObjectDeletedError, ContainerNotEmpty, QueryNotExecuted, MemoryManagerError
from .memmanager import MemoryManager

__author__ = 'Athanasios Anastasiou'
__email__ = 'athanastasiou@gmail.com'
__license__ = 'MIT'
__package__ = 'neoads'
__version__ = pkg_resources.get_distribution('neoads').version
