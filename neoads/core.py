"""
Core functionality of neoads.

Provides the basic entities required to represent neoads as well as "hosted" domain objects.

"Hosted" domain objects are those that can be referenced by neoads without knowing anything 
about their internal structure.


:author: Athanasios Anastasiou 
:date: Jan 2018
"""


import neomodel
from . import exception
import datetime
import hashlib
import uuid


class PersistentValue(neomodel.StructuredNode):
    """
    Base type for all entities that are persistent via ``neoads``.
    """
    def _neoads_hash(self):
        """
        Returns a hash for the entity it represents (if it is hashable).
        """
        raise TypeError(f"Unhashable type {self.__class__.__name__}")

    def _pre_action_check(self, action):
        """
        Handles pre-action checks specifically for neoads based models so that neoads exceptions with more informative
        messages can be raised.
        """
        try:
            super()._pre_action_check(action)
        except ValueError as ve:
            if "on deleted node" in ve.args[0]:
                raise exception.ObjectDeletedError(f"Operation {action} attempted on deleted object")
            if "on unsaved node" in ve.args[0]:
                raise exception.ObjectUnsavedError(f"Operation {action} attempted on unsaved object")


class Value(PersistentValue):
    """
    Base type for all persistent values within ``neoads``.

    :param value: The actual value
    :type value: Any
    """
    value = None

    @property
    def value(self):
        return self.value


class ValuePair(PersistentValue):
    """
    """
    p_left = neomodel.RelationshipTo(PersistentValue, "CAR", cardinality=neomodel.One)
    p_right = neomodel.RelationshipTo(PersistentValue, "CDR", cardinality=neomodel.One)

    @property
    def left(self):
        return self.p_left[0]

    @property
    def right(self):
        return self.p_right[0]

    def cons(self, left=None, right=None):
        # If left or right are ValueReference then first de-reference and then connect
        self.save()
        if left is not None:
            self.p_left.connect(left)
        if right is not None:
            self.p_right.connect(right)
        return self


class ValueReference(neomodel.StructuredNode):
    """
    Points to a value.

    :param name: String, default value is a uuid4 tag
    """
    name = neomodel.StringProperty(unique_index=True, default=uuid.uuid4)
    ref = neomodel.RelationshipTo(PersistentValue, "HAS_VALUE", cardinality=neomodel.One)

    @property
    def value(self):
        return self.ref[0]

    def anonymous_ref(self):
        """
        Initialises this reference into an anonymous reference
        """
        self.save()
        return self

    def named_ref(self, name):
        self.name = name
        self.save()
        return self

    def point_to(self, another_value):
        self.ref.connect(another_value)
        return self


class DomainValue(PersistentValue):
    """
    Base type for all persistent values that belong to the "hosted" domain.
    """
    
    def _neoads_hash(self):
        """
        The hash of an entity is the hash of its property's values.

        .. note::

            Obviously, the order the hash is derived by affects its value and this is why the values are sorted by 
            attribute name first.

        """
        # return hash(tuple(map(lambda x: x[1], sorted(self.__properties__.items(), key=lambda x: x[0]))))
        return int(hashlib.sha256(str(tuple(map(lambda x: x[1], sorted(self.__properties__.items(), key=lambda x: x[0])))).encode("utf-8")).hexdigest(), base=16)

      

