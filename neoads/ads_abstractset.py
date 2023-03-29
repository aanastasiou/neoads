"""
Definition of the AbstractSet.

:author: Athanasios Anastasiou 
:date: Mar 2023

"""

import neomodel
from .core import PersistentElement
from . import exception
from .ads_core import AbstractStructItem, CompositeAbstract


class SetItem(AbstractStructItem):
    """
    A struct item that is an element of a set.

    A set item maintains its item's ``hash_value`` for fast lookups.
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

    .. warning::

        Attractive as its functionality might be, the Set lacks functions to populate it with CYPHER queries
        (e.g. from_query). The key problem with that is that the item's hash_value cannot be set consistently (no
        similar function in APOC) at the server side.

    
    **TODO:** However, it might be possible to establish a hash-like user procedure in CYPHER at server side which could be
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

        .. warning::

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

        .. note::

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

        .. warning::
        
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


        .. warning::

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

      
        .. warning::

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

        .. warning::

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

        .. warning::

            The item **must be hashable**.

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
