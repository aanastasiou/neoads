"""
Core functionality of neoads.

Provides the basic entities required to represent neoads as well as "hosted" domain objects.

"Hosted" domain objects are those that can be referenced by neoads but those that neoads has no need of knowing their
internal structure.

:author: Athanasios Anastasiou 
:date: Jan 2018
"""

from .core import ElementVariable
from . import exception
import neomodel
import datetime
import hashlib
import pandas


class VariableComposite(ElementVariable):
    """
    Base type for variables that are of Composite data types.

     Composite data types represent values that are composite (e.g. arrays).
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
        Clears the array by writing an empty sequence to its value
        :return:
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

    Note: To avoid over complicating things, a neoads "number" is a double precision real number.
    """
    value = neomodel.ArrayProperty(neomodel.FloatProperty())
    
    def __setitem__(self, key, value):
        if isinstance(value, float) or isinstance(value, int):
            return super().__setitem__(key, value)
        else:
            raise TypeError(f"CompositeArrayNumber assignment expects float received {type(value)}")

    def from_query_IDs(self, query, refresh=True, auto_reset=False):
        """
        Executes a special type of query with the only purpose to populate the array of numbers with the IDs of the
        entities in the query.

        Consequently, the query must have a specific structure. The general pattern of the query is as follows:

        MATCH Array WITH Array [query] WITH Array,collect(id(ListItem)) as ItemIds set Array.value=ItemIds;

        Where [query] is an INCOMPLETE Cypher MATCH query with at least one named Node that is called "ListItem".
        That named node is the node whose id will be catalogued in the list.

        WARNING: The predefined "Array" must be propagated in subsequent withs for it to go all the way to the other
                 side of the query and finish.

        NOTE:
            This functionality is not meant to substitute double linked lists for collections of articles because it
            relies heavily on Node IDs which are subject to change. Instead, this functionality is meant to ASSIST in
            creating Double Linked Lists of articles FROM lists of IDs

        :param query: String, a Cypher Query making specific reference to ListItem.
        :param refresh: Boolean (True), Whether this action should trigger a refresh or not
        :param auto_reset: Whether to clear the list if it is found to be populated
        :return:
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
    """
    value = neomodel.ArrayProperty(neomodel.DateProperty())
    
    def __setitem__(self, key, value):
        if isinstance(value, datetime.date):
            return super().__setitem__(key,value)
        else:
            raise TypeError(f"CompositeArrayDate assignment expected datetime received {type(value)}")


class CompositeArrayObjectBase(VariableComposite):
    """
    Represents a query that upon instantiation returns results in some form.

    Not to be isntantiated directly by user code.

    Note:
          This data structure stores the actual query that returns the results, NOT the results themselves.
          For this reason, the results might be different every time the query is executed (because the backend data
          may have changed).
    """
    # Notice the unique index here: If a verbatim query exists in the database already then just re-use that one.
    value = neomodel.StringProperty(unique_index=True, required=True)
    _result = None

    def execute(self, params=None, refresh=True):
        """
        Executes the query and returns the result.
        The data type of specific categories of queries is specialised further by descendants of
        CompositeArrayObjectBase

        :return: Query Results
        """
        if not refresh and self._result is not None:
            return self._result

        items, attr = neomodel.db.cypher_query(self.value, params=params, resolve_objects=self.resolve_objects)
        if self.result_as == "list":
            # If a list is requested, you return a list of dictionaries which
            # allows accessors of the form myList[0]["someNode"]
            self._result = list(map(lambda x: dict(zip(attr, x)), items))
        elif self.result_as == "dict":
            self._result = dict(map(lambda x: (x[0], dict(zip(attr[1:], x[1:]))), items))
        elif self.result_as == "pandas":
            # If the return is a pandas dataframe then noCasting is ignored
            self._result = pandas.DataFrame(columns=attr, data=items, index=None)
        else:
            raise NotImplementedError(f"{self._result} return value requested. Currently supported are (pandas,dict,list)")

        return self._result

    def __getitem__(self, item):
        """
        Accessor operator for query results. Retrieves a returned item by index.

        :param item: Index.
        :type item: Index data type.
        :return: Query result value at index.
        """
        if self._result is None:
            raise exception.QueryNotExecuted(f"Item {item} was requested from a query that "
                                             "has not yet been executed.")
        return self._result[item]


class CompositeArrayObjectList(CompositeArrayObjectBase):
    """
    Represents a query that returns results as a Python list of dictionaries.
    It is therefore possible to request item by integer index followed by column name.
    """
    def execute(self, params=None, refresh=True):
        if not refresh and self._result is not None:
            return self._result

        items, attr = neomodel.db.cypher_query(self.value, params=params, resolve_objects=True)
        self._result = list(map(lambda x: dict(zip(attr, x)), items))
        return self._result


class CompositeArrayObjectDict(CompositeArrayObjectBase):
    """
    Represents a query that returns results as a Python dict.

    Note:
        By convention, the first return value from the query is the key and all others become the value. Therefore,
        "duplicates" (items that are returned but happen to have the same key) are removed.

    WARNING:
        The functionality of this data type removes duplicates AT THE CLIENT SIDE, NOT AT THE SERVER SIDE.
    """
    def execute(self, params=None, refresh=True):

        if not refresh and self._result is not None:
            return self._result

        items, attr = neomodel.db.cypher_query(self.value, params=params, resolve_objects=True)
        self._result = dict(map(lambda x: (x[0], dict(zip(attr[1:], x[1:]))), items))
        return self._result


class CompositeArrayObjectDataFrame(CompositeArrayObjectBase):
    """
    Represents a query that returns results as a pandas DataFrame.

    Note:
        The DataFrame does not have an index and access is through pandas' `iloc`.
    """
    def execute(self, params=None, refresh=True):
        if not refresh and self._result is not None:
            return self._result

        items, attr = neomodel.db.cypher_query(self.value, params=params, resolve_objects=True)
        self._result = pandas.DataFrame(columns=attr, data=items, index=None)
        return self._result


