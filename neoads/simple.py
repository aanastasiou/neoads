"""
Definitions for data types that represent a single number (e.g. 4.56) and 
a simple date (e.g. 01/01/1970)


Simple data types represent values that are single and atomic (for example, 
a single double precision number).


:author: Athanasios Anastasiou 
:date: Jan 2018
"""

from .core import Value
import neomodel
import hashlib
import datetime


class SimpleValue(Value):
    """
    Base type for simple data values.
    """

    def __init__(self, value):
        """
        Default implementation for the assignment operator
        """
        if name is not None:
            super().__init__(value=value)
        else:
            super().__init__(value=value)
        self.save()

    def _neoads_hash(self):
        """
        Compute the hash value of SimpleValue as the sha256 of its string representation.

        In general, simple values are expected to be able to be converted to 
        string in a straightforward way.
        """
        return int(hashlib.sha256(str(self.value).encode("utf-8")).hexdigest(), base=16)
    
    def __str__(self):
        return str(self.value)


class IntegerValue(SimpleValue):
    """
    A typical single integer number.

    :param value: An integer
    :type value: neomodel.IntegerProperty

    """
    value = neomodel.IntegerProperty(index=True)

    def __init__(self, value):
        if not isinstance(value, int):
            raise TypeError(f"IntegerValue initialisation expects int received {type(value)}")
        super().__init__(value=int(value))


class FloatValue(SimpleValue):
    """
    A typical single Real number.

    :param value: A float 
    :type value: neomodel.FloatProperty

    """
    value = neomodel.FloatProperty(index=True)

    def __init__(self, value):
        if not isinstance(value, float):
            raise TypeError(f"FloatValue initialisation expects float received {type(value)}")
        super().__init__(value=float(value))

        

class DateValue(SimpleValue):
    """
    A typical date value.

    :param value: A date.
    :type value: neomodel.DateProperty
    """

    value = neomodel.DateProperty(index=True)

    def __init__(self, value, **kwargs):
        if not isinstance(value, datetime.date):
            raise TypeError(f"DateValue initialisation expects datetime.date received {type(value)}")
        super().__init__(value=value, **kwargs)

