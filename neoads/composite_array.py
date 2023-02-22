"""
Definitions for composite data types. These represent values that are composite (e.g. arrays).


:author: Athanasios Anastasiou 
:date: Jan 2018
"""

from .core import ElementVariable
from . import exception
import neomodel
import datetime
import hashlib


class VariableComposite(ElementVariable):
    """
    Base type for variables that are of Composite data types.

    ``VariableComposite`` are implemented on top of ``neomodel`` array "properties" (with the exception of
    ``CompositeString``) and therefore correspond to native Neo4J arrays.
    """

    def __init__(self, value, name=None, **kwargs):
        """
        Default implementation for the assignment operator for composite variables

        :param value:
        """
        if name is not None:
            super().__init__(value=value, name=name, **kwargs)
        else:
            super().__init__(value=value, **kwargs)

    def clear(self):
        """
        Clears the array by writing an empty sequence to its value.
        """
        self._pre_action_check("clear")
        # Notice here the level at which the query occurs. This method occurs in VariableComposite and is supposed to
        # apply to all descendants. At the CYPHER level, this is applied via the query labels.
        self.cypher(f"MATCH (array:{':'.join(self.labels())}{{name:'{self.name}'}}) SET array.value=[]")
        # After applying the clear operation, perform a neomodel::refresh to update the status of the object.
        self.refresh()

    def __getitem__(self, key):
        self._pre_action_check('__getitem__')

        if key>=0 and key<len(self.value):
            return self.value[key]
        else:
            raise IndexError(f"{self.__class__.__name__} index out of range")
            
    def __setitem__(self, key, value):
        self._pre_action_check('__setitem__')
        if key>=0 and key<len(self.value):
            self.value[key] = value
        else:
            raise IndexError(f"{self.__class__.__name__} assignment index out of range")
        return self  
        
    def __len__(self):
        """
        Returns the length of a composite variable which is simply the length of its value.
        """
        self._pre_action_check('__len__')
        return len(self.value)


class CompositeString(VariableComposite):
    """
    A typical string.

    Strings are represented as composite objects to support indexing naturally.

    :param value: The actual string value
    :type value: neomodel.StringProperty
    """
    value = neomodel.StringProperty(index=True)

    def __init__(self, value, name=None, **kwargs):
        if not isinstance(value, str):
            raise TypeError(f"CompositeString initialisation expects str received {type(value)}")
        super().__init__(value=value, name=name, **kwargs)
    
    def _neoads_hash(self):
        """
        Returns the hash of the string value.
        """
        self._pre_action_check('__hash__')
        return int(hashlib.sha256(self.value.encode("utf-8")).hexdigest(), base=16)
    
    
class CompositeArrayString(VariableComposite):
    """
    A native Neo4j array of strings.

    :param value: An array of strings
    :type value: neomodel.ArrayProperty
    """
    value = neomodel.ArrayProperty(neomodel.StringProperty())
    
    def __setitem__(self, key, value):
        if isinstance(value, str):
            return super().__setitem__(key,value)
        else:
            raise TypeError(f"CompositeArrayString assignment expects str, received {type(value)}")


class CompositeArrayNumber(VariableComposite):
    """
    A native Neo4j array of numbers.

    :param value: An array of Real numbers.
    :type value: neomodel.ArrayProperty
    """
    value = neomodel.ArrayProperty(neomodel.FloatProperty())
    
    def __setitem__(self, key, value):
        if isinstance(value, float) or isinstance(value, int):
            return super().__setitem__(key, value)
        else:
            raise TypeError(f"CompositeArrayNumber assignment expects float received {type(value)}")

    def from_query_IDs(self, query, refresh=True, auto_reset=False):
        """
        Executes a special type of query to populate the array of numbers with the IDs of the
        entities in the query.

        Consequently, the query must have a specific structure. The general pattern of the query is as follows:

        ``MATCH Array WITH Array [query] WITH Array,collect(id(ListItem)) as ItemIds set Array.value=ItemIds;``

        Where ``[query]`` is an INCOMPLETE Cypher MATCH query with at least one named Node that is called "ListItem".
        That named node is the node whose id will be catalogued in the list.

        .. warning::

            The predefined "Array" must be propagated in subsequent withs for it to go all the way to the other
            side of the query and finish.


        .. note::
            
            This functionality is not meant to substitute double linked lists for collections of articles because it
            relies heavily on Node IDs which are subject to change. Instead, this functionality is meant to ASSIST in
            creating Double Linked Lists of articles FROM lists of IDs

        :param query: A Cypher Query making specific reference to ListItem.
        :type query: str
        :param refresh: Whether this action should trigger a refresh or not
        :type refresh: bool
        :param auto_reset: Whether to clear the list if it is found to be populated
        :type auto_reset: bool
        :returns: self
        """
        # TODO: MED, This is another remnant of an "older" way of doing things. With the advent of ArrayObjectBase,
        #       and its descendants, what this function achieved can be simplified even more. So, DLList's corresponding
        #       `from` function is going to have to also begin to accept ArrayObjectBase objects for initialisation.
        self._pre_action_check("from_query_IDs")

        if auto_reset:
            self.clear()
        elif len(self)>0:
            raise exception.ContainerNotEmpty(f"Attempted to reset non-empty CompositeArrayNumber {self.name}")

        self.cypher(f"MATCH (array:{':'.join(self.labels())}{{name:'{self.name}'}}) "
                    f"WITH array {query} "
                    f"WITH array, collect(distinct id(ListItem)) AS item_ids SET array.value=item_ids")

        if refresh:
            self.refresh()

        return self
    

class CompositeArrayDate(VariableComposite):
    """
    A native Neo4J array of dates.

    :param value: The actual array value
    :type value: neomodel.ArrayProperty
    """
    value = neomodel.ArrayProperty(neomodel.DateProperty())
    
    def __setitem__(self, key, value):
        if isinstance(value, datetime.date):
            return super().__setitem__(key,value)
        else:
            raise TypeError(f"CompositeArrayDate assignment expected datetime received {type(value)}")



