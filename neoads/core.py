"""
Core functionality of neoads.

Provides the basic entities required to represent neoads as well as "hosted" domain objects.

"Hosted" domain objects are those that can be referenced by neoads but those that neoads has no need of knowing their
internal structure.

:author: Athanasios Anastasiou 
:date: Jan 2018
"""


import neomodel
from neoads import exception
import pandas
import datetime
import hashlib


class PersistentElement(neomodel.StructuredNode):
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


class ElementVariable(PersistentElement):
    """
    Base type for persistent elements of the types provided by neoads.

    A persistent data element has a logical name that is used to refer to it and this name must be unique across a
    database instance.
    """
    value = None

    name = neomodel.UniqueIdProperty()


class ElementDomain(PersistentElement):
    """
    Base type for all persistent elements that belong to the "hosted" domain.
    """
    
    def _neoads_hash(self):
        """
        The hash of an entity is the hash of its property's values.

        NOTE: Obviously, the order the hash is derived by affects its value and this is why the values are sorted by
        attribute name first.
        """
        # return hash(tuple(map(lambda x: x[1], sorted(self.__properties__.items(), key=lambda x: x[0]))))
        return int(hashlib.sha256(str(tuple(map(lambda x: x[1], sorted(self.__properties__.items(), key=lambda x: x[0])))).encode("utf-8")).hexdigest(), base=16)


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

        
class CompositeAbstract(VariableComposite):
    """
    Base class for representing abstract data types.

    Note:
        Abstract data types can be of any length (supported by the database) and they can point to ANY system element.
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
    value = neomodel.RelationshipTo("PersistentElement", "ABSTRACT_STRUCT_ITEM_VALUE")
      

class SetItem(AbstractStructItem):
    """
    A struct item that is an element of a set.

    A set item maintains its item's `hash_value` for fast lookups.
    """
    # The hash value is not essential for the data structure but it is essential for insertions and deletions
    # hash_value = neomodel.IntegerProperty(index=True, required=True)
    hash_value = neomodel.StringProperty(index=True, required=True)

    def __init__(self, hash_value, **kwargs):
        """
        Initialises a SetItem object by ensuring that the hash_value will be turned into a hex string.

        NOTE:
            The hexadecimal should be lowercase formated.

        :param hash_value:
        :param kwargs:
        """
        if isinstance(hash_value, int):
            # Convert it to a string
            hash_value = f"{hash_value:x}"
            super().__init__(hash_value=hash_value, **kwargs)


class AbstractSet(CompositeAbstract):
    """
    A Set of UNIQUE elements.

    WARNING:
        Attractive as its functionality might be, the Set lacks functions to populate it with CYPHER queries
        (e.g. from_query). The key problem with that is that the item's hash_value cannot be set consistently (no
        similar function in APOC) at the server side.

    TODO:
        However, it might be possible to establish a hash-like user procedure in CYPHER at server side which could be
        invoked by neoads to implement such queries server side too. (With APOC's sha this can definitely be done now)
    """
    elements = neomodel.RelationshipTo("SetItem", "SET_ELEMENT")

    def from_abstractset(self, an_abstractSet, auto_reset=False):
        """
        Initialises an abstract set from another abstract set.

        :param an_abstractSet:
        :param auto_reset:
        :return: AbstractSet (self)
        """
        self._pre_action_check("from_abstractset")

        # Check that an_abstractSet is of the right type
        if not issubclass(type(an_abstractSet), AbstractSet):
            raise TypeError(f"from_abstractset expects 'AbstractSet' received {type(an_abstractSet)}")

        # Empty the current values
        if auto_reset:
            self.clear()
        elif len(self)>0:
            raise exception.ContainerNotEmpty(f"Attempted to reset non empty AbstractSet {self.name}")

        this_set_labels = ":".join(self.labels())
        this_set_name = self.name
        other_set_labels = ":".join(an_abstractSet.labels())
        other_set_name = an_abstractSet.name

        self.cypher(f"MATCH (this_set:{this_set_labels}{{name:'{this_set_name}'}}), "
                    f"(other_set:{other_set_labels}{{name:'{other_set_name}'}})-[:SET_ELEMENT]->"
                    "(an_element:AbstractStructItem:SetItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->"
                    "(an_element_value) CREATE (this_set)-[:SET_ELEMENT]->"
                    "(:AbstractStructItem:SetItem{hash_value:an_element.hash_value})-[:ABSTRACT_STRUCT_ITEM_VALUE]->"
                    "(an_element_value)")

        self.refresh()
        return self

    # def from_query(self, query, auto_reset=False):
    #     """
    #     Populates a Set from a query
    #
    #     WARNING!!!: This function is not working because there is no way to establish the hash on Neo4Js side
    #     :param query:
    #     :param auto_reset:
    #     :return:
    #     """
    #     self._pre_action_check("from_query")
    #
    #     if auto_reset:
    #         self.clear()
    #     elif len(self)>0:
    #         raise exception.ContainerNotEmpty("Attempted to reset non empty AbstractSet {}".format(self.name))
    #
    #     self.cypher("MATCH (a_set:AbstractSet{{name:'{nme}'}}) with a_set {match_query} with a_set, SetItem, count(SetItem) as SetItem_CNT CREATE (a_set)-[:SET_ELEMENT]->(an_item:SetItem:AbstractStructItem{{hash_value:hash(SetItem)}})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(SetItem);".format(**{"nme" : self.name,"match_query":query}))
    #     self.refresh()
    #     return self

    def from_hash_nodeid_list(self, a_hash_nodeid_list, auto_reset=False):
        """
        Initialises an abstract set from a list of hash, Node ID tuples

        NOTE:
            Not to be called directly.

        :param a_hash_nodeid_list: A list of tuples
        :type a_hash_nodeid_list: list
        :param auto_reset: Whether to clear the contents of the set automatically
        :type auto_reset: boolean
        :return: AbstractSet (self)
        """
        # Check that this object is saved
        self._pre_action_check("from_hash_nodeid_list")

        # Check that a_hash_nodeid_list is a python list
        if not isinstance(a_hash_nodeid_list, list):
            raise TypeError(f"from_python expects 'list' received {type(a_hash_nodeid_list)}")

        # Empty the current values
        if auto_reset:
            self.clear()
        elif len(self)>0:
            raise exception.ContainerNotEmpty(f"Attempted to reset non empty AbstractSet {self.name}")

        #self.cypher("WITH {the_hash_nodeid_list} AS hash_nodeid_list UNWIND hash_nodeid_list AS hash_nodeid_item MERGE (a_set:AbstractSet{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(a_set_element:AbstractStructItem:setElement{{hash_value:hash_nodeid_list[0]}}) ON CREATE MATCH (a_value_node) where id(a_value_node)=hash_node_list[1] CREATE (a_set_element)-[:ABSTRACT_STRUCT_VALUE]->(a_value_node) ON MATCH MATCH (a_set_element:setElement)-[r:ABSTRACT_STRUCT_VALUE]->(some_node) detach delete r MATCH (a_value_node) where id(a_value_node)=hash_node_list[1] CREATE (a_set_element)-[:ABSTRACT_STRUCT_VALUE]->(a_value_node)".format(**{"the_hash_nodeid_list":str(a_hash_nodeid_list).replace("(","[").replace(")","]"),"this_set_name":self.name}))
        # TODO: HIGH Turn the static labels to dynamic ones
        the_hash_nodeid_list = str(a_hash_nodeid_list).replace("(", "[").replace(")", "]")
        this_set_name = self.name

        self.cypher(f"MATCH (a_set:AbstractSet{{name:'{this_set_name}'}}) "
                    f"WITH a_set,{the_hash_nodeid_list} AS hash_nodeid_list "
                    "UNWIND hash_nodeid_list AS hash_nodeid_item "
                    "MATCH (a_value_node) WHERE id(a_value_node)=hash_nodeid_item[1] "
                    "CREATE (a_set)-[:SET_ELEMENT]->"
                    "(a_set_element:AbstractStructItem:SetItem{hash_value:hash_nodeid_item[0]})-[:ABSTRACT_STRUCT_ITEM_VALUE]->"
                    "(a_value_node)")
        return self

    def __len__(self):
        """
        Returns the size of the set.

        :return: int
        """
        self._pre_action_check('__len__')
        return len(self.elements)

    def __eq__(self, other):
        """
        Set equality.

        NOTE:
            Set equality for Sets of the same length is tested here purely on the basis of identical hashes.

        :param other: AbstractSet
        :return: bool
        """
        if not type(other) is AbstractSet:
            raise TypeError(f"Unsupported operand type(s) for ==: '{type(self)}' and '{type(other)}'")

        self._pre_action_check("__eq__")
        other._pre_action_check("__eq__")

        # If the set lengths do not match then there is no point in proceeding with checking for their contents.
        if self.__len__() != other.__len__():
            return False

        nme_left = self.name
        nme_right = other.name

        is_equal, _ = self.cypher(f"MATCH (:AbstractSet{{name:'{nme_left}'}})-[:SET_ELEMENT]->(u:SetItem) "
                                  "WITH u.hash_value AS u_hash ORDER BY u_hash "
                                  f"MATCH (:AbstractSet{{name:'{nme_right}'}})-[:SET_ELEMENT]->(v:SetItem) "
                                  "WITH collect(u_hash) AS u_hash_array, v.hash_value AS v_hash ORDER BY v_hash "
                                  "RETURN u_hash_array=collect(v_hash)")
        # Alternatively, to push even the length check to the server, the query could be changed slightly to first form
        # BOTH arrays and then test them for equality and length when they are both formed. (Otherwise it leads to
        # re-evaluation and it is not efficient. But that would still mean that a full check would have to run even if
        # the lengths are different, although this can be circumvented by first running a length query and THEN running
        # the equality check (but this brings us back to what is happening now).
        #
        # Alternatively, the check could be performed client side with:
        # return [setelement.hash_value for setelement in self.elements] == \
        #        [setelement.hash_value for setelement in other.elements]
        return bool(is_equal[0][0])

    def __or__(self, other):
        """
        Set union.

        :param other: The other AbstractSet that participates in the union.
        :type other: AbstractSet
        :return: AbstractSet
        """
        if not type(other) is AbstractSet:
            raise TypeError(f"Unsupported operand type(s) for |: '{type(self)}' and '{type(other)}'")

        self._pre_action_check("__or__")
        other._pre_action_check("__or__")
        new_set = AbstractSet().save()
        if len(self)==0:
            new_set.from_abstractset(other, auto_reset=True)
        else:
            new_set.from_abstractset(self, auto_reset=True)

        this_set_name = new_set.name
        other_set_name = other.name
        # TODO: HIGH, Turn static labels to dynamic ones
        self.cypher(f"MATCH (this_set:AbstractSet{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(this_set_item:AbstractStructItem) "
                    "WITH this_set,COLLECT(this_set_item.hash_value) AS this_set_hash_nums "
                    f"MATCH (other_set:AbstractSet{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(other_set_item:AbstractStructItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value_node) "
                    "WHERE NOT other_set_item.hash_value IN this_set_hash_nums "
                    "CREATE (this_set)-[:SET_ELEMENT]->(:AbstractStructItem:SetItem{hash_value:other_set_item.hash_value})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value_node);")
        new_set.refresh()
        return new_set

    def __and__(self, other):
        """
        Set intersection.

        :param other: The other AbstractSet that participates in the intersection.
        :type other: AbstractSet
        :return: AbstractSet
        """
        if not type(other) is AbstractSet:
            raise TypeError(f"Unsupported operand type(s) for &: '{type(self)}' and '{type(other)}'")

        self._pre_action_check("__and__")
        other._pre_action_check("__and__")
        new_set = AbstractSet().save()
        this_set_name = self.name
        other_set_name = other.name
        new_set_name = new_set.name
        # TODO; HIGH, Turn static labels to dynamic ones
        self.cypher(f"MATCH (this_set:AbstractSet{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(an_element:AbstractStructItem:SetItem) WITH COLLECT(an_element.hash_value) as this_set_hash_values MATCH (other_set:AbstractSet{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(another_element:AbstractStructItem:SetItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_set_value) WHERE another_element.hash_value IN this_set_hash_values WITH another_element,a_set_value MATCH (new_set:AbstractSet{{name:'{new_set_name}'}}) CREATE (new_set)-[:SET_ELEMENT]->(:AbstractStructItem:SetItem{{hash_value:another_element.hash_value}})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_set_value)")
        new_set.refresh()
        return new_set

    def __sub__(self, other):
        """
        Set difference.

        :param other: The other AbstractSet that participates in the difference.
        :type other: AbstractSet
        :return: AbstractSet
        """
        if not type(other) is AbstractSet:
            raise TypeError(f"Unsupported operand type(s) for -: '{type(self)}' and '{type(other)}'")

        self._pre_action_check("__sub__")
        other._pre_action_check("__sub__")
        new_set = AbstractSet().save()

        other_set_name = other.name
        this_set_name = self.name
        new_set_name = new_set.name
        # TODO; HIGH, Turn static labels to dynamic ones
        self.cypher(f"MATCH (other_set:AbstractSet{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(other_element:AbstractStructItem:SetItem) WITH COLLECT(other_element.hash_value) AS other_set_hash_values MATCH (this_set:AbstractSet{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(this_element:AbstractStructItem:SetItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value) WHERE NOT this_element.hash_value IN other_set_hash_values WITH this_element, a_value MATCH (new_set:AbstractSet{{name:'{new_set_name}'}}) CREATE (new_set)-[:SET_ELEMENT]->(:AbstractStructItem:SetItem{{hash_value:this_element.hash_value}})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value)")
        new_set.refresh()
        return new_set

    def __xor__(self, other):
        """
        Set symmetric difference
        :param other: The other AbstractSet that participates in the symmetric difference.
        :type other: AbstractSet
        :return: AbstractSet
        """
        if not type(other) is AbstractSet:
            raise TypeError(f"Unsupported operand type(s) for ^: '{type(self)}' and '{type(other)}'")

        self._pre_action_check("__xor__")
        other._pre_action_check("__xor__")
        new_set = AbstractSet().save()

        other_set_name = other.name
        this_set_name = self.name
        new_set_name = new_set.name

        # Symmetric difference implemented as two difference queries here (A-B)|(B-A)
        # A-B        
        # TODO; HIGH, Turn static labels to dynamic ones
        self.cypher(f"MATCH (other_set:AbstractSet{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(other_element:AbstractStructItem:SetItem) WITH COLLECT(other_element.hash_value) AS other_set_hash_values MATCH (this_set:AbstractSet{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(this_element:AbstractStructItem:SetItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value) WHERE NOT this_element.hash_value IN other_set_hash_values WITH this_element, a_value MATCH (new_set:AbstractSet{{name:'{new_set_name}'}}) CREATE (new_set)-[:SET_ELEMENT]->(:AbstractStructItem:SetItem{{hash_value:this_element.hash_value}})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value)")

        other_set_name = self.name
        this_set_name = other.name

        # B-A
        # TODO; HIGH, Turn static labels to dynamic ones
        self.cypher(f"MATCH (other_set:AbstractSet{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(other_element:AbstractStructItem:SetItem) WITH COLLECT(other_element.hash_value) as other_set_hash_values MATCH (this_set:AbstractSet{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(this_element:AbstractStructItem:SetItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value) WHERE NOT this_element.hash_value IN other_set_hash_values WITH this_element, a_value MATCH (new_set:AbstractSet{{name:'{new_set_name}'}}) CREATE (new_set)-[:SET_ELEMENT]->(:AbstractStructItem:SetItem{{hash_value:this_element.hash_value}})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value)")
        
        # The queries operate on the same "new_set"
        new_set.refresh()
        return new_set

    def contains_hash(self, a_hash):
        """
        Determines if the set contains a specific hash value.

        :param a_hash: The hash value to test
        :type a_hash: int
        :return: bool
        """
        # self._pre_action_check("delete")
        nme = self.name
        itm_hash = a_hash

        # TODO; HIGH, Turn static labels to dynamic ones
        # NOTE: Hash operations need '{itm_hash:x}' because hash is a string
        return len(self.cypher(f"MATCH (a_set:AbstractSet{{name:'{nme}'}})-[:SET_ELEMENT]->(an_element:SetItem) WHERE an_element.hash_value='{itm_hash:x}' RETURN an_element")[0]) > 0

    def __contains__(self, an_item):
        """
        Determines if the set contains a specific item.

        :param an_item: An object
        :type an_item: PersistentElement
        :return: bool
        """
        #TODO: Med, Check that an_item is PersistentElement
        an_item_hash = an_item._neoads_hash()
        return self.contains_hash(an_item_hash)

    def _add_element(self, an_item, a_hash):
        """
        Adds a new element to the set.

        WARNING:
            Not meant to be called directly.

        :param an_item: An object that is to be added to the set.
        :type an_item: PersistentElement
        :param a_hash: Hash value
        :type a_hash: int
        :return: AbstractSet (self)
        """
        # Create a new set item
        new_set_item = SetItem(hash_value=a_hash).save()
        # Connect the value
        new_set_item.value.connect(an_item)
        # Actually make the SetItem part of this set.
        self.elements.connect(new_set_item)
        return self

    def add_with_hash(self, an_item, a_hash):
        """
        Adds an item to the set with a particular hash value.

        Not meant to be called directly. Used by the AbstractMap.
        :param an_item: An object that is to be added to the set
        :type an_item: PersistentElement
        :param a_hash: A hash value
        :type a_hash: int
        :return:
        """
        if not isinstance(an_item, PersistentElement):
            raise TypeError(f"AbstractSet.add_with_hash() assignment expected PersistentElement, received {type(an_item)}")
        # Get the hash of the key
        if not self.contains_hash(a_hash):
            self._add_element(an_item, a_hash)

    def retrieve_by_hash(self, a_hash):
        """
        Retrieves the value that the set element points to given the set element's hash value.

        NOTE:
            Not meant to be called directly. Used by AbstractMap.

        :param a_hash: An object's hash value
        :type a_hash: int
        :return: PersistentElement
        """
        if self.contains_hash(a_hash):
            nme = self.name
            itm_hash = a_hash
            # TODO; HIGH, Turn static labels to dynamic ones
            return self.cypher(f"MATCH (a_set:AbstractSet{{name:'{nme}'}})-[:SET_ELEMENT]->(an_element:SetItem) WHERE an_element.hash_value='{itm_hash:x}' return an_element")[0][0]
        raise KeyError(f"AbstractSet does not contain item with hash {a_hash:x}")

    def remove_by_hash(self, a_hash):
        """
        Removes an element from the set, given its hash value.

        NOTE:
            Not meant to be called directly. Used by AbstractMap.

        :param a_hash: An object's hash value
        :type a_hash: int
        :return: AbstractSet (self)
        """
        if self.contains_hash(a_hash):
            nme = self.name
            itm_hash = a_hash
            # TODO; HIGH, Turn static labels to dynamic ones
            self.cypher(f"MATCH (a_set:AbstractSet{{name:'{nme}'}})-[:SET_ELEMENT]->(an_element:SetItem) WHERE an_element.hash_value='{itm_hash:x}' DETACH DELETE an_element")
        else:
            raise KeyError(f"AbstractSet does not contain item with hash {a_hash:x}")
        return self

    def add(self, an_item):
        """
        Adds an item to the set. Similar to Python's set.add().

        NOTE:
            The item must be hashable.

        :param an_item: An object to be added to the AbstractSet.
        :type an_item: PersistentElement

        :return: AbstractSet (self)
        """
        if not isinstance(an_item, PersistentElement):
            raise TypeError(f"AbstractSet.add() expected PersistentElement, received {type(an_item)}")
        # Get the hash of the key
        if not self.__contains__(an_item):
            self._add_element(an_item, an_item._neoads_hash())
        return self

    def clear(self):
        """
        Clears the set.
        """
        nme = self.name
        # TODO: HIGH, Turn static labels to dynamic ones
        self._pre_action_check("clear")
        self.cypher(f"MATCH (a_set:AbstractSet{{name:'{nme}'}})-[r1:SET_ELEMENT]->(el_item:SetItem)-[r2:ABSTRACT_STRUCT_ITEM_VALUE]->() DETACH DELETE r2,el_item,r1")

    def destroy(self):
        """
        Clears the set and removes it from the DBMS completely.
        """
        self._pre_action_check("destroy")
        self.clear()
        self.delete()


# TODO: MED, Also needs initialisation by two existing AbstractSets, which could help with the recovery of stray
#            elements.
class AbstractMap(CompositeAbstract):
    """
    A very simple mapping that maps a hash value (that can be computed by any hashable) to an entity.

    NOTE:
        Implemented via two AbstractSets, one for the keys and one for the values.
    """

    keys_set = neomodel.RelationshipTo("AbstractSet", "KEYS_SET")
    values_set = neomodel.RelationshipTo("AbstractSet", "VALUES_SET")

    def _init_map(self):
        """
        Initialises the map.

        NOTE:
            Because of the way the object hierarchy is set up, an uninitialised set can exist without actual reference
            to the two AbstractSets it requires to function properly. **BUT**, when the time comes for the map to
            operate it has to ensure that it has its two sets initialised properly.

            An AbstractMap maintains links to two anonymous sets. If those links were to be severed, it would be
            possible for those sets to be collected and completely erased by the garbage collector.
        """
        new_keys_set = AbstractSet().save()
        new_values_set = AbstractSet().save()
        self.keys_set.connect(new_keys_set)
        self.values_set.connect(new_values_set)

    def __len__(self):
        """
        Returns the length of the mapping.

        :return: int
        """
        self._pre_action_check("__len__")
        try:
            return len(self.keys_set[0])
        except IndexError:
            return 0

    def __delitem__(self, key):
        """
        Removes the entry associated with a particular key from the AbstractMap.

        :param key: An object that will be looked up as `key`.
        :type key: PersistentElement

        :return:
        """
        self._pre_action_check("__delitem__")
        key_set_element = SetItem.inflate(self.keys_set[0].retrieve_by_hash(key._neoads_hash())[0])
        value_set_element = SetItem.inflate(self.values_set[0].retrieve_by_hash(key._neoads_hash())[0])
        key_set_element.delete()
        value_set_element.delete()

    def __contains__(self, item):
        """
        Determines if the mapping contains a specific key.

        NOTE:
            This basically re-uses the IN operator for AbstractSet.

        :param item: An object
        :type item: PersistentElement
        :return:
        """
        self._pre_action_check("__contains__")
        try:
            return self.keys_set[0].contains_hash(item._neoads_hash())
        except IndexError:
            self._init_map()
            return False

    def __getitem__(self, key):
        """
        Returns the value associated with the key.

        :param key: Any hashable object.
        :type key: PersistentElement
        :return: PersistentElement
        """
        self._pre_action_check("__getitem__")
        try:
            if key in self.keys_set[0]:
                set_item_element = self.values_set[0].retrieve_by_hash(key._neoads_hash())
                return SetItem.inflate(set_item_element[0]).value[0]
        except IndexError:
            self._init_map()

        raise KeyError("{key}")

    def __setitem__(self, key, value):
        """
        Sets / resets a key to be pointing to a specific value.

        NOTE:
            `value` should be a PersistentElement that has already been **saved** in the database.
            The AbstractSet must have been instantiated properly before any operations are applied to it.

        :param key: A `key` object.
        :type key: PersistentElement
        :param value: A `value` object.
        :type value: PersistentElement
        :return:
        """
        self._pre_action_check("__setitem__")
        if not isinstance(value, PersistentElement):
            raise TypeError(f"AbstractMap assignment expected PersistentElement, received {type(value)}")
        try:
            if not key in self.keys_set[0]:
                self.keys_set[0].add(key)
                self.values_set[0].add_with_hash(value, key._neoads_hash())
            else:
                # The key does exist in the map and its value has to be updated
                key_hash = key._neoads_hash()
                self.values_set[0].remove_by_hash(key_hash)
                self.values_set[0].add_with_hash(value, key_hash)
        except IndexError:
            # The map has not been initialised yet
            self._init_map()
            self.keys_set[0].add(key)
            self.values_set[0].add_with_hash(value, key._neoads_hash())

    def from_keyvalue_node_query(self, a_query, auto_reset=False):
        """
        Instantiates an AbstractMap via a query.

        NOTE:
            The query must have a specific structure and return two arrays, one for the keys and one for the values.
            For example:

            SimpleNumber(1).save()
            SimpleNumber(2).save()
            SimpleNumber(3).save()

            CompositeString("One").save()
            CompositeString("Two").save()
            CompositeString("Three").save()

            Q = AbstractSet(name="ASET").save()

            Q.from_keyvalue_node_query("MATCH (a:ElementVariable) WHERE a.value IN [1,2,3] WITH collect(a) AS Keys
            MATCH (b:ElementVariable) WHERE b.value IN ["One","Two","Three"] WITH Keys, collect(b) as Values")

            The objects in the array will have to be inflated in to Python, their hash calculated and then used to
            construct the sets.

        :param a_query: A **COMPLETE** CYPHER query.
        :type a_query: str
        :param auto_reset:
        :type auto_param: bool
        :return: AbstractMap (self)
        """
        self._pre_action_check("from_keyvalue_node_query")

        if auto_reset or len(self.keys_set)==0:
            self.clear()
        elif len(self)>0:
            raise exception.ContainerNotEmpty(f"Attempted to reset non empty AbstractMap {self.name}")
        # Query the database to retrieve the key/value pairs
        # TODO: HIGH, Must check if a_query contains the variables Key and Value and does not contain a "return"
        keyvalue_list, _ = neomodel.db.cypher_query(a_query, resolve_objects=True)
        # Check if the returned arrays have the same length
        if len(keyvalue_list[0][0][0])!=len(keyvalue_list[0][1][0]):
            raise Exception("Arrays not the same size")
        else:
            # Pre-compute the hash values
            hash_values = [f"{an_object._neoads_hash():x}" for an_object in keyvalue_list[0][0][0]]
            # Build the key set
            self.keys_set[0].from_hash_nodeid_list(list(zip(hash_values, [an_object.id for an_object in keyvalue_list[0][0][0]])), auto_reset=True)
            # Build the value set
            self.values_set[0].from_hash_nodeid_list(list(zip(hash_values, [an_object.id for an_object in keyvalue_list[0][1][0]])), auto_reset=True)
            self.refresh()
        return self

    def clear(self):
        """
        Clears the map.
        """
        self._pre_action_check("clear")
        try:
            self.values_set[0].clear()
            self.keys_set[0].clear()
        except IndexError:
            self._init_map()

    def destroy(self):
        """
        Clears the map and completely removes it from the DBMS.
        """
        self._pre_action_check("destroy")
        try:
            key_set = self.keys_set[0]
            value_set = self.values_set[0]
            self.keys_set.disconnect(key_set)
            self.values_set.disconnect(value_set)
            key_set.destroy()
            value_set.destroy()
        except IndexError:
            pass
        # The key or value sets might not have been created yet in which case we just delete the map
        self.delete()


class DLListItem(AbstractStructItem):
    """
    A struct item of a doubly linked list.
    """
    # Pointer to the next item in the list
    prv = neomodel.RelationshipTo("DLListItem", "DLL_PRV")
    # Pointer to the previous item in the list
    nxt = neomodel.RelationshipTo("DLListItem", "DLL_NXT")


class AbstractDLList(CompositeAbstract):
    """
    A doubly linked list with indexing.

    NOTE:
        Although the list is Doubly Linked, only the list's `head` is preserved with the List entry.
    """
    head = neomodel.RelationshipTo("DLListItem", "DLL_NXT")
    length = neomodel.IntegerProperty(default=0)

    def __len__(self):
        """
        Returns the length of the list.
        :return: int
        """
        self._pre_action_check('__len__')
        return self.length

    def destroy(self):
        """
        Clears the list and completely removes it from the DBMS.
        """
        self.clear()
        self.delete()

    def clear(self):
        """
        Clears the list.

        NOTE:
            To delete the list itself, use destroy()
        """
        self._pre_action_check('clear')
        nme = self.name
        # TODO; HIGH, Turn static labels to dynamic ones
        self.cypher(f"MATCH (a_list:AbstractDLList{{name:'{nme}'}})-[:DLL_NXT*]-(data_item:DLListItem) DETACH DELETE data_item")
        self.length = 0
        self.save()

    def __getitem__(self, item_index):
        """
        Implements indexed lookup.

        :param item_index: An integer index that if not within limits, raises IndexError exception
        :type item_index: int
        :return: PersistentElement
        """

        # TODO: HIGH, Does this need a `_pre_action_check` or would that slow things down?
        # NOTE: Here, I am always reaching out from the head but it is faster to reach out from the current position.
        # NOTE: MyList[0] takes 0.00518 and MyList[3000] takes 0.2510 to finish.

        # Find the DL List item
        if item_index < 0 or item_index > self.length:
            raise IndexError(f"Index {item_index} out of bounds in a list of length {self.length}")
        #.format(**{"idx": item_index + 1, "self": "{self}"})
        idx = item_index + 1 # The 'item+1' is required to offset the hop from the head to the first item.
        # TODO; HIGH, Turn static labels to dynamic ones
        list_record = self.cypher(f"MATCH (a)-[:DLL_NXT*{idx}]->(b:DLListItem) WHERE ID(a)=$self RETURN b")
        item_value = DLListItem.inflate(list_record[0][0][0])
        # TODO: HIGH, This must return the actual object
        return item_value.value[0]

    def __delitem__(self, item_index):
        """
        Deletes a specific item from the list.

        NOTE:
            The item is selected by index and it can be wherever in a list.

        :param key: Index to the item in the list to be deleted
        :type key: int
        """
        # TODO: LOW, Reduce code duplication with __getitem__ in retrieving the DL list item.
        if item_index < 0 or item_index > self.length:
            raise IndexError(f"Index {item_index} out of bounds in a list of length {self.length}")
            # The 'item+1' is required to offset the hop from the head to the first item.
        # First of all locate the item ...
        # TODO; HIGH, Turn static labels to dynamic ones
        list_record = self.cypher(f"MATCH (a)-[:DLL_NXT*{item_index + 1}]->(b:DLListItem) WHERE ID(a)=$self RETURN b")
        item_object = DLListItem.inflate(list_record[0][0][0])
        # ...disconnect it from the list depending on its location...
        if len(item_object.nxt) == 1 and len(item_object.prv) == 1:
            # This is a middle item
            # Bypass it
            item_object.prv[0].nxt.reconnect(item_object,item_object.nxt[0])
            item_object.nxt[0].prv.reconnect(item_object,item_object.prv[0])

        if len(item_object.nxt) == 1 and len(item_object.prv) == 0:
            # This is a head item
            # Have the list's head point to the next item
            self.head.reconnect(item_object, item_object.nxt[0])

        if len(item_object.nxt) == 0 and len(item_object.prv) == 1:
            # TODO: HIGH, Remove this branch
            # This is a tail item
            # Nothing special needs to be done
            pass
        # ... delete the item
        item_object.delete()
        # Adjust the length of the list
        self.length -= 1
        # Save the modification to this list
        self.save()

    def project_as(self,this_list_known_as, projection_known_as, projected_field=None, pass_through=None):
        """
        Returns a query that converts the Doubly Linked List to a native neo4j list so that it can participate in
        subsequent queries. This function returns part of a query that can be concatenated with other lists as part of
        a bigger query.

        NOTE:
            Collects the values of projected_field from this list into a new, sequential array that is being known
            as projection_known_as.

            This is the only way to implement "IN" at server side as somehow CYPHER has to iterate the array to extract
            specific values from it.

        :param pass_through: List of other parameters that have to be propagated through this part of the query.
        :type pass_through: list
        :param this_list_known_as: The logical name that this list will be made known as, server-side.
        :type this_list_known_as: str
        :param projected_field: The list item value field that is to be extracted from this list.
        :type projected_field: str
        :param projection_known_as: The logical name that the generated list will be made known as, server-side.
        :type projection_known_as: str
        :return: str (CYPHER query fragment)
        """

        # If the projected field is none, then the id of the item that the list is holding is to be emitted
        if projected_field is None:

            nme = self.name
            labels = ":".join(self.labels())
            listIdentifier = this_list_known_as
            projectedField = projected_field
            projectionKnownAs = projection_known_as

            # TODO; HIGH, Turn static labels to dynamic ones
            item_query = f"MATCH ({listIdentifier}:{labels}{{name:'{nme}'}}) WITH {listIdentifier} MATCH ({listIdentifier})-[:DLL_NXT*]->({listIdentifier}_listItem:DLListItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->({listIdentifier}_listItemValue) WITH collect(id({listIdentifier}_listItemValue)) as {projectionKnownAs}  "
        else:
            # TODO; HIGH, Turn static labels to dynamic ones
            item_query = "MATCH ({listIdentifier}:{labels}{{name:'{nme}'}}) WITH {listIdentifier} MATCH ({listIdentifier})-[:DLL_NXT*]->({listIdentifier}_listItem:DLListItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->({listIdentifier}_listItemValue) WITH collect({listIdentifier}_listItemValue.{projectedField}) as {projectionKnownAs}  "
        # If there are pass through variables add them in the final query
        if pass_through is not None:
            pass_through_items = ",".join(pass_through)
            modified_with = f"WITH {pass_through_items},"
            split_query = item_query.split("WITH")
            item_query = split_query[0]+modified_with+split_query[1]+modified_with+split_query[2]
        return item_query

    def with_this_list_as(self, this_list_known_as, other_lists = None):
        """
        Starts a CYPHER query in which an AbstractDLList is exposed with a given name.

        :param this_list_known_as: The name that this list will be made known as, server-side.
        :type this_list_known_as: str
        :param other_lists: Other lists that may precede this particular list.
        :type other_lists: list
        :return: str (CYPHER query fragment)
        """
        #.format(nme=self.name, list_known_as=this_list_known_as, other_lists=",{}".format(",".join(other_lists)) if other_lists is not None else "")
        #",{}".format(",".join(other_lists)) if other_lists is not None else "")

        nme = self.name
        list_known_as = this_list_known_as
        other_lists = ",{','.join(other_lists) if other_lists is not None else ''}"

        # TODO: HIGH, Propagate the lists correctly.
        return f"MATCH (aList:AbstractDLList{{name:'{nme}'}}) WITH aList{other_lists} MATCH (aList)-[:DLL_NXT*]->(:DLListItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(aList_listItemValue) WITH collect(aList_listItemValue) AS {list_known_as}{other_lists}"

    def iterate_by_query(self, this_list_known_as):
        """
        Generates a query that iterates over all items of the list.

        NOTE:
            This can be used to "trigger" further queries / operations over each item within the list.

        WARNING:
            These are the ACTUAL ITEMS that the list is holding. If this list is pointing to other lists, those
            lists are not automatically UNWINDED!!!!

        EXAMPLE:
            neomodel.db.cypher_query(list1.iterate_by_query("pubmed")+"MATCH (Author1:Author)-[:AUTHOR]-
                                                            (pubmed_listItemValue)-[:AUTHOR]-(Author2:Author)
                                                            where Author1<>Author2 return count(Author1)")


        :param this_list_known_as: An identifier by which this list will be known within the query. It is possible
                                   to concatenate many of these from different lists and therefore should not have name
                                   collisions.
        :type this_list_known_as: str
        """
        # TODO: HIGH, Must verify if this match does indeed reach all of the items in the list or it skips the last one.
        # TODO; HIGH, Turn static labels to dynamic ones
        return f"MATCH ({listIdentifier}:AbstractDLList{{name:'{self.name}'}}) WITH {this_list_known_as} MATCH ({this_list_known_as})-[:DLL_NXT*]->({this_list_known_as}_listItem:DLListItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->({this_list_known_as}_listItemValue) WITH {this_list_known_as}_listItemValue "

    def extend_by_merging(self,another_dlList):
        """
        Concatenates this list with `another_dlList` and **ERASES** another_dlList as a separate list from the backend.

        :param another_dlList: The identifier or object of a list that already exists on the DBMS.
        :type another_dlList: str or AbstractDLList.
        :return: AbstractDLList
        """

        if type(another_dlList) is str:
            other_list = AbstractDLList.nodes.get(name = another_dlList)[0]
        elif type(another_dlList) is AbstractDLList:
            other_list = another_dlList
        else:
            raise TypeError("extend_by_merging expected AbstractDLList received {type(another_dlList)}")

        # If both lists are non-empty, then it is worth going ahead with a full merge
        if len(self) > 0 and len(other_list) > 0:
            # Retrieve the tail STRUCT item of THIS list.
            # The tail struct item has DLL_PRV but no DLL_NXT
            # TODO; HIGH, Turn static labels to dynamic ones
            this_list_tail_item = DLListItem.inflate(self.cypher(f"MATCH (a_list:AbstractDLList{{name:'{self.name}'}})-[:DLL_NXT*]-(data_item:DLListItem) WHERE NOT (data_item)-[:DLL_NXT]->() RETURN data_item")[0][0][0])
            # Retrieve the head STRUCT item of the other list.
            # The head item is readily available
            other_list_head_item = other_list.head[0]
            # Effect the concatenation
            this_list_tail_item.nxt.connect(other_list_head_item)
            other_list_head_item.prv.connect(this_list_tail_item)
            # Adjust the length of this list.
            self.length += other_list.length
            # Delete the **ENTRY** of the other list
            other_list.cypher(f"MATCH (a:AbstractDLList{{name:'{other_list.name}'}}) "
                              "DETACH DELETE a")
            # Update this list so that its length gets written back
            self.save()
        else:
            # If this list is empty but other_list is not then there is no point in going ahead with a full merge
            if len(self) > 0:
                # Grab the other list's head
                self.head.connect(other_list.head[0])
                # Copy its length too
                self.length = other_list.length
                # Get rid of the other list's entry ONLY! (delete vs destroy)
                # Delete the **ENTRY** of the other list
                other_list.cypher(f"MATCH (a:AbstractDLList{{name:'{other_list.name}'}}) "
                                  "DETACH DELETE a")
            # Update the info of this list
                self.save()
            else:
                # If other_list is empty, then again there is no point in going ahead with a full merge
                other_list.destroy()
            # If both lists are empty, no further action is taken
        return self

    def append(self, an_element):
        """
        Appends any PersistentElement to the Doubly Linked List.

        :param an_element: PersistentElement
        :return: AbstractDLList (self)
        """
        self._pre_action_check("append")
        if not isinstance(an_element, PersistentElement):
            raise TypeError(f"AbstractDLList.append() expected PersistentElement, received {type(an_element)}.")

        # Prepare a new list item
        new_list_item = DLListItem().save()
        # Connect it to the element
        new_list_item.value.connect(an_element)

        # If this list is empty, then `an_element` will become the list's head
        if len(self) == 0:
            self.head.connect(new_list_item)
            self.length +=1
        else:
            # This list is not empty and the new item will have to be added to the list's tail.
            # Find the tail
            # TODO: HIGH, Reduce duplication here by adding a _get_tail() to AbstractDLList or alternatively establish
            #       two pointers for faster operation
            this_list_tail_item = DLListItem.inflate(self.cypher(f"MATCH (a_list:AbstractDLList{{name:'{self.name}'}})-[:DLL_NXT*]-(data_item:DLListItem) "
                                                                 "WHERE NOT (data_item)-[:DLL_NXT]->() RETURN data_item")[0][0][0])
            # Connect it to the list (so that the new element becomes the list's tail)
            this_list_tail_item.nxt.connect(new_list_item)
            new_list_item.prv.connect(this_list_tail_item)
            # Adjust the length of this list
            self.length += 1
        # Update the list because either of the above branches lead to an update.
        self.save()
        return self

    def from_query(self, query, auto_reset=False, no_duplicates=False):
        """
        Creates a doubly linked list at server side.

        NOTE:
            The list's items point to the return result of `query`. The query **MUST** return PersistentElement and be
            a CYPHER READ query.

        WARNING:
            At the moment, the way the CYPHER queries that build the list are expressed, they seem to "explode" with
            the number of items returned by from_query(..., query). So use with caution.

            If the query returns duplicates, these are retained in the list because a list does not behave like a set.

         EXAMPLE: "MATCH (ListItem:Institute)-[:CITY]-(:City)-[:IN_COUNTRY]-(:Country{countryName:'Australia'})"
                   with a possible WHERE clause too


        :param no_duplicates: Whether or not to retain potential ListItem duplicates that might be returned by `query`
        :type no_duplicates: bool
        :param query: A CYPHER READ query **WITHOUT** the return clause. The entity that is to be pointed to by list
                      items should be named ListItem.
        :return: AbstractDLList (self)
        """
        self._pre_action_check("from_query")
        if auto_reset:
            self.clear()
        elif len(self)>0:
            raise exception.ContainerNotEmpty(f"Attempted to reset non empty AbstractDLList {self.name}")

        dprem_query_fragment = {False:"",True:",count(ListItem) as ListItem_CNT "}

        # TODO; HIGH, Turn static labels to dynamic ones
        # Ensure initial conditions on the present list
        self.cypher(f"MATCH (a_list:AbstractDLList:CompositeAbstract:VariableComposite:ElementVariable:PersistentElement{{name:'{self.name}'}}) SET a_list.length=0")
        # Create list items and index them sequentially
        #.format(**{"nme" : self.name,"match_query":query,"dup_removal":dprem_query_fragment[no_duplicates]})
        nme = self.name
        match_query = query
        dup_removal = dprem_query_fragment[no_duplicates]

        # TODO: HIGH, if match_query contains WITH it must be ensured that aList is propagated in that query, otherwise this would fail (see also from_id_array)
        self.cypher(f"MATCH (a_list:AbstractDLList:CompositeAbstract:VariableComposite:ElementVariable:PersistentElement{{name:'{nme}'}}) WITH a_list {match_query} WITH a_list, ListItem{dup_removal} CREATE (a_list)-[:TEMP_LINK{{of_list:a_list.name,item_id:a_list.length}}]->(an_item:DLListItem:AbstractStructItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(ListItem) SET a_list.length=a_list.length+1")
        
        # Create the double linked list connections
        # Create forwards connections
        self.cypher(f"MATCH (a_list:AbstractDLList:CompositeAbstract:VariableComposite:ElementVariable:PersistentElement{{name:'{self.name}'}})-[r1:TEMP_LINK{{of_list:a_list.name}}]->(this_item:DLListItem:AbstractStructItem) WHERE r1.item_id<a_list.length WITH a_list,r1,this_item MATCH (a_list)-[r2:TEMP_LINK{{of_list:a_list.name}}]->(next_item:DLListItem:AbstractStructItem) WHERE r2.item_id=r1.item_id+1 CREATE (this_item)-[:DLL_NXT]->(next_item)")

        # Create backwards connections
        self.cypher(f"MATCH (a_list:AbstractDLList:CompositeAbstract:VariableComposite:ElementVariable:PersistentElement{{name:'{self.name}'}})-[r1:TEMP_LINK{{of_list:a_list.name}}]->(this_item:DLListItem:AbstractStructItem) WHERE r1.item_id>0 WITH a_list,r1,this_item MATCH (a_list)-[r2:TEMP_LINK{{of_list:a_list.name}}]->(previous_item:DLListItem:AbstractStructItem) WHERE r2.item_id=r1.item_id-1 CREATE (this_item)-[:DLL_PRV]->(previous_item)")

        # Connect the items to the head of the list
        self.cypher(f"MATCH (a_list:AbstractDLList{{name:'{self.name}'}})-[r:TEMP_LINK{{of_list:a_list.name,item_id:0}}]->(a_list_item:DLListItem) WITH a_list,a_list_item CREATE (a_list)-[:DLL_NXT]->(a_list_item)")

        # Delete the temporary links
        self.cypher(f"MATCH (a_list:AbstractDLList{{name:'{self.name}'}})-[r:TEMP_LINK{{of_list:a_list.name}}]->(:DLListItem) DELETE r")
        # Now, length has changed, so this entity needs to be refreshed
        self.refresh()
        return self

    def from_id_array(self, array_of_ids, auto_reset=False):
        """
        Initialises the doubly linked list from a numeric array of node IDs.

        NOTE:
            This array_of_ids is usually constructed via a call to CompositeArrayNumber.from_query_IDs().
            Because of the dangers associated with maintaining IDs for long intervals it is best if these two are
            called in quick succession.

        :param array_of_ids: The name or actual object of an array of IDs.
        :type array_of_ids: str or CompositeArrayNumber
        :return: AbstractDLList (self)
        """
        self._pre_action_check("from_id_array")
        if auto_reset:
            self.clear()
        elif len(self)>0:
            raise exception.ContainerNotEmpty(f"Attempted to reset non empty AbstractDLList {self.name}")
        if isinstance(array_of_ids, str):
            # The parameter is a string, get the actual object
            array_object = CompositeArrayNumber.nodes.get(name=array_of_ids)
        elif isinstance(array_of_ids, CompositeArrayNumber):
            array_object = array_of_ids
        else:
            raise TypeError(f"from_id_array expected str or CompositeArrayNumber, received {type(array_of_ids)}")

        labels = ":".join(array_object.labels())
        name = array_object.name

        # Notice here that I am simply re-using from_query
        self.from_query(f"MATCH (array:{labels}{{name:'{name}'}}) WITH a_list, array MATCH (ListItem) WHERE id(ListItem) in array.value")
        return self
