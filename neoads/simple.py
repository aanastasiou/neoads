"""
Core functionality of neoads.

Provides the basic entities required to represent neoads as well as "hosted" domain objects.

"Hosted" domain objects are those that can be referenced by neoads but those that neoads has no need of knowing their
internal structure.

:author: Athanasios Anastasiou 
:date: Jan 2018
"""

from .core import ElementVariable
import neomodel
import hashlib
import datetime


class VariableSimple(ElementVariable):
    """
    Base type for variables that are of Simple data types.

    Simple data types represent values that are single and atomic (for example, a single double precision number).
    """

    def __init__(self, value, name = None):
        """
        Default implementation for the assignment operator

        :param value:
        """
        if name is not None:
            super().__init__(value=value, name=name)
        else:
            super().__init__(value=value)

    def _neoads_hash(self):
        self._pre_action_check('hash')
        # return hash(self.value)
        return super().__hash__()


class SimpleNumber(VariableSimple):
    """
    A typical single number.

    Note: To avoid over complicating things, a neoads "number" is a double precision real number.
    """
    value = neomodel.FloatProperty(index=True)

    def __init__(self, value, name=None):
        if not isinstance(value, (float, int)):
            raise TypeError(f"SimpleNumber initialisation expects int or float received {type(value)}")
        super().__init__(value=float(value), name=name)

    def _neoads_hash(self):
        self._pre_action_check('hash')
        return int(hashlib.sha256(str(self.value).encode("utf-8")).hexdigest(), base=16)


class SimpleDate(VariableSimple):
    value = neomodel.DateProperty(index=True)

    def __init__(self, value, name=None, **kwargs):
        if not isinstance(value, datetime.date):
            raise TypeError(f"SimpleDate initialisation expects datetime.date received {type(value)}")
        super().__init__(value=value, name=name, **kwargs)

    def _neoads_hash(self):
        self._pre_action_check('hash')
        return int(hashlib.sha256(str(self.value).encode("utf-8")).hexdigest(), base=16)


