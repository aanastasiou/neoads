"""
Definitions for composite "object" data types.

The classes defined in this module can be used to store a specific **neo4j cypher query** and 
"address" it as if it was a ``dict``, ``list`` or ``pandas.DataFrame``



:author: Athanasios Anastasiou 
:date: Jan 2018
"""
import neomodel
from .composite_array import VariableComposite


class CompositeArrayObjectBase(VariableComposite):
    """
    Represents *a query* that upon instantiation returns results in a particular form.

    .. warning::
    
        Not to be instantiated directly by user code.

    .. note::

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
        return items, attr

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
    It is therefore possible to request an item by integer index followed by column name.
    """
    def execute(self, params=None, refresh=True):
        items, attr = super().execute(params, refresh)
        return list(map(lambda x: dict(zip(attr, x)), items))


class CompositeArrayObjectDict(CompositeArrayObjectBase):
    """
    Represents a query that returns results as a Python dict.

    .. note::
    
        By convention, the first return value from the query is the key and all others become the value. Therefore,
        "duplicates" (items that are returned but happen to have the same key) are removed.


    .. warning::

        The functionality of this data type removes duplicates AT THE CLIENT SIDE, NOT AT THE SERVER SIDE.
    """
    def execute(self, params=None, refresh=True):
        items, attr = super().execute(params, refresh)
        return dict(map(lambda x: (x[0], dict(zip(attr[1:], x[1:]))), items))


try:
    import pandas

    class CompositeArrayObjectDataFrame(CompositeArrayObjectBase):
        """
        Represents a query that returns results as a pandas DataFrame.
    
        .. note::
        
            The DataFrame does not have an index and access is through pandas' `iloc`.
    
        """
        def execute(self, params=None, refresh=True):
            items, attr = super().execute(params, refresh) 
            return pandas.DataFrame(columns=attr, data=items, index=None)
except ImportError:
    pass


