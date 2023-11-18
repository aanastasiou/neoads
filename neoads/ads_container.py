"""
Definitions of neoads core objects to support a "memory model" over neo4j.

The module defines both end-user data structures as well as intermediate (or helper) data structures.


:author: Athanasios Anastasiou 
:date: Dec 2023
"""

import neomodel
from .composite_array import VariableComposite
from . import exception


class CompositeAbstract(VariableComposite):
    """
    Base class for representing abstract data structures.

    .. note::

        Abstract data structures can be of any length (supported by the database) and they can point to ANY system element.
    """

    def __init__(self, name=None, **kwargs):
        # TODO: HIGH, This instantiation is a remnant of an older way of instantiating these classes that needs revision
        #       but also, this way of instantiating the class attached a 'value' field when it is not necessary. This
        #       might be a minor bug with neomodel (has been flagged as of Mar 20) but it might be avoidable just with
        #       a simple restructuring of the code.

        # TODO: HIGH, Related to the previous todo item, the constructor needs to be reviewed because CompositeArray,
        #       uses the convention of accepting a value by default and a name optionally but CompositeAbstract
        #       descendants do not require a default value and therefore anything passed in the constructor is basically
        #       the name of the variable. Need to do something about this inconsistency.
        if name is not None:
            super().__init__(None, name=name, **kwargs)
        else:
            super().__init__(None, **kwargs)

    def __len__(self):
        raise NotImplementedError(f"len() not implemented on {self.__class__.__name__}")

    def delete(self):
        """
        Attempts to delete a CompositeAbstract object. If it contains data it raises an exception.

        :return: Nothing
        """
        self._pre_action_check("delete")
        if self.__len__() > 0:
            raise exception.ContainerNotEmpty(f"Attempted to delete non empty container {self.name} of type {self.__class__.__name__}.")
        else:
            super().delete()


class AbstractStructItem(neomodel.StructuredNode):
    """
    Base class for helper entities that are used by the abstract data types.

    For example, the double linked list item, each item of the set etc.
    """
    # By knowing that abstract data structure items are attached on "ABSTRACT_STRUCT_ITEM_VALUE" relationships
    # it also becomes very easy to look for "orphan" entities whether it is for garbage collection or any other
    # purpose of the memory manager.
    value = neomodel.RelationshipTo("PersistentElement", "ABSTRACT_STRUCT_ITEM_VALUE", cardinality=neomodel.One)
    hash = neomodel.StringProperty()

