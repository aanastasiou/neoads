"""
Definitions for data types that represent a single number (e.g. 4.56) and 
a simple date (e.g. 01/01/1970)


Simple data types represent values that are single and atomic (for example, 
a single double precision number).


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
    """

    def __init__(self, value, name = None):
        """
        Default implementation for the assignment operator
        """
        if name is not None:
            super().__init__(value=value, name=name)
        else:
            super().__init__(value=value)

    def _neoads_hash(self):
        """
        Compute the hash value of VariableSimple as the sha256 of its string representation.

        In general, simple variable values are expected to be able to be converted to 
        string in a straightforward way.
        """
        return int(hashlib.sha256(str(self.value).encode("utf-8")).hexdigest(), base=16)


class SimpleNumber(VariableSimple):
    """
    A typical single number.

    **Note:** To avoid over complicating things, a neoads "number" is a 
          double precision real number.

    :param value: A double precision real number
    :type value: neomodel.FloatProperty

    """
    value = neomodel.FloatProperty(index=True)

    def __init__(self, value, name=None):
        if not isinstance(value, (float, int)):
            raise TypeError(f"SimpleNumber initialisation expects int or float received {type(value)}")
        super().__init__(value=float(value), name=name)


class SimpleInteger(VariableSimple):
    """
    A typical single integer number.

    :param value: An integer
    :type value: neomodel.IntegerProperty

    """
    value = neomodel.IntegerProperty(index=True)

    def __init__(self, value, name=None):
        if not isinstance(value, int):
            raise TypeError(f"SimpleInteger initialisation expects int received {type(value)}")
        super().__init__(value=int(value), name=name)


class SimpleFloat(VariableSimple):
    """
    A typical single Real number.

    :param value: An integer
    :type value: neomodel.FloatProperty

    """
    value = neomodel.FloatProperty(index=True)

    def __init__(self, value, name=None):
        if not isinstance(value, float):
            raise TypeError(f"SimpleFloat initialisation expects float received {type(value)}")
        super().__init__(value=float(value), name=name)

        

class SimpleDate(VariableSimple):
    """
    A typical single date.

    :param value: The date that this element represents.
    :type value: neomodel.DateProperty
    """

    value = neomodel.DateProperty(index=True)

    def __init__(self, value, name=None, **kwargs):
        if not isinstance(value, datetime.date):
            raise TypeError(f"SimpleDate initialisation expects datetime.date received {type(value)}")
        super().__init__(value=value, name=name, **kwargs)

