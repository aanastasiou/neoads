"""
Definition of the ``AbstractSet``.

An ``AbstractSet`` is represented in Neo4j as follows:

.. graphviz::

    digraph foo {
        graph [
            rankdir=LR
        ]
        node [
              shape=record
             ]

        ADS_Set [
            label = "{{a:AbstractSet|+name}}"
            ]

        ADS_SetItem [
            label="{{b:SetItem|+ hash_value}}"
        ]

        ADS_ElementDomain [
            label="{{c:PersistentElement|}}"
        ]

        ADS_Set -> ADS_SetItem [label=SET_ELEMENT headlabel="0..*"]
        ADS_SetItem -> ADS_ElementDomain [label=ABSTRACT_STRUCT_ITEM_VALUE]

    }

* Where ``PersistentElement`` can be **ANY** entity in the data model deriving from ``PersistentElement``.
  For more details please see :ref:`datamodeling` 


:author: Athanasios Anastasiou 
:date: Mar 2023
"""

import neomodel
from .core import PersistentElement
from . import exception
from .ads_core import AbstractStructItem, CompositeAbstract


class AbstractSet(CompositeAbstract):
    """
    A Set of UNIQUE elements.
    """

    @property
    def elements(self):
        return None

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

        #TODO: HIGH, this needs to be handled with from_query
        self.cypher(f"MATCH (this_set:{this_set_labels}{{name:'{this_set_name}'}}), "
                    f"(other_set:{other_set_labels}{{name:'{other_set_name}'}})-[:DLL_NXT*]->"
                    "(an_element:AbstractStructItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->"
                    "(an_element_value) CREATE (this_set)-[:SET_ELEMENT]->"
                    "(:AbstractStructItem:SetItem{hash_value:an_element.hash_value})-[:ABSTRACT_STRUCT_ITEM_VALUE]->"
                    "(an_element_value)")

        self.refresh()
        return self

    def from_query(self, query, auto_reset=False):
        """
        Populates a Set from a query at server side.

        .. warning:: 
            
            Use of this function requires the Neo4j server to be using `APOC <https://neo4j.com/docs/apoc/current/overview/apoc/>`_.
            If APOC is not available, see AbstractSet's ``.add()``


        .. note::

            The set's elements are the entities that are "selected" by ``query``. 
            The ``query`` **MUST** bind a ``SetElement`` entity which itself would have to be a ``PersistentElement`` and should be an *incomplete* CYPHER READ query.

        **EXAMPLE:**

         ::

            "MATCH (SetElement: CompositeString)"
                      with a possible WHERE clause too

        Notice here:

        * This query would create a Set of all the unique ``CompositeString`` entities in 
          the database.

        * This query is *incompete*. It only contains the MATCH statement without the usually necessary `return` clause.



        :param query: A CYPHER READ query **WITHOUT** the `return` clause. The elements of the set should be bind as `SetElement`.
        :type query: str
        :param auto_reset: Whether to re-use the set node by first clearing the contents
                           of the Set prior to populating it.
        :type auto_reset: bool
        :raises ContainerNotEmpty: When ``from_query`` is called on an already populated Set. Use ``auto_reset=True`` to discard the current Set elements and reset it to the result of ``from_query``.
        :return: AbstractSet (self) 
        """
        self._pre_action_check("from_query")
    
        if auto_reset:
            self.clear()
        elif len(self)>0:
            raise exception.ContainerNotEmpty("Attempted to reset non empty AbstractSet {}".format(self.name))
        
        this_set_name = self.name
        this_set_labels = ":".join(self.labels())

        # TODO: HIGH, Amend CompositeAbstract and then edit this query to take into account the composite hash
        # TODO: HIGH, `from_query` can now go into CompositeAbstract
    
        self.cypher(f"MATCH (a_set:{this_set_labels}{{name:'{this_set_name}'}}) WITH a_set {query} with a_set, SetElement, properties(SetElement) as p,  "
                    f"keys(properties(SetElement)) as k order by k with a_set, COLLECT([SetElement, apoc.util.sha256([reduce(v=\"\", m in [u in k where u<>\"name\"|u+p[u]]|v+m)])]) as SetElementAndHash "
                    f"UNWIND SetElementAndHash as SetElementAndHashItem with a_set, SetElementAndHashItem order by SetElementAndHashItem[1] "
                    f"WITH a_set, collect(SetElementAndHashItem) as OrderedSetElementAndHash with a_set, [i in range(0, size(OrderedSetElementAndHash)-1) WHERE i=0 or OrderedSetElementAndHash[i][1] <> OrderedSetElementAndHash[i-1][1]|OrderedSetElementAndHash[i]] as FinalSetElementAndHash "
                    # From this point onwards, the queries are exactly the same to the DLList ones.
                    f"UNWIND [k in range(0, size(FinalSetElementAndHash)-1) | [a_set, k, FinalSetElementAndHash[k][0]]] as node_data "
                    f"WITH node_data[0] AS origin, node_data[1] AS set_item_idx, node_data[2] AS set_item "
                    f"CREATE (origin)-[:TEMP_LINK{{of_set:origin.name,item_id:set_item_idx}}]->(:AbstractStructItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(set_item)")

        # Create the double linked connections
        # Create forwards connections
        self.cypher(f"MATCH (a_set:{this_set_labels}{{name:'{this_set_name}'}})-[r1:TEMP_LINK{{of_set:a_set.name}}]->(this_item:AbstractStructItem) "
                    f"WITH a_set,r1,this_item MATCH (a_set)-[r2:TEMP_LINK{{of_set:a_set.name}}]->(next_item:AbstractStructItem) "
                    f"WHERE r2.item_id=r1.item_id+1 CREATE (this_item)-[:DLL_NXT]->(next_item)")

        # Create backwards connections
        self.cypher(f"MATCH (a_set:{this_set_labels}{{name:'{this_set_name}'}})-[r1:TEMP_LINK{{of_set:a_set.name}}]->(this_item:AbstractStructItem) WHERE r1.item_id>0 "
                    f"WITH a_set,r1,this_item MATCH (a_set)-[r2:TEMP_LINK{{of_set:a_set.name}}]->(previous_item:AbstractStructItem) "
                    f"WHERE r2.item_id=r1.item_id-1 CREATE (this_item)-[:DLL_PRV]->(previous_item)")
        
        # Connect the items to the head of the list
        self.cypher(f"MATCH (a_set:{this_set_labels}{{name:'{this_set_name}'}})-[r:TEMP_LINK{{of_set:a_set.name,item_id:0}}]->(a_set_item:AbstractStructItem) "
                    f"WITH a_set,a_set_item CREATE (a_set)-[:DLL_NXT]->(a_set_item)")

        # Delete the temporary links
        self.cypher(f"MATCH (a_set:{this_set_labels}{{name:'{this_set_name}'}})-[r:TEMP_LINK{{of_set:a_set.name}}]->(:AbstractStructItem) DELETE r")
        # Now, length has changed, so this entity needs to be refreshed
        self.refresh()
        return self

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

        lbl_left = ":".join(self.labels())
        lbl_right = ":".join(other.labels())

        is_equal, _ = self.cypher(f"MATCH (:{lbl_left}{{name:'{nme_left}'}})-[:SET_ELEMENT]->(u:SetItem) "
                                  "WITH u.hash_value AS u_hash ORDER BY u_hash "
                                  f"MATCH (:{lbl_right}{{name:'{nme_right}'}})-[:SET_ELEMENT]->(v:SetItem) "
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
        new_set = self.__class__().save()
        if len(self)==0:
            new_set.from_abstractset(other, auto_reset=True)
        else:
            new_set.from_abstractset(self, auto_reset=True)

        this_set_name = new_set.name
        other_set_name = other.name
        this_set_labels = ":".join(new_set.labels())
        other_set_labels = ":".join(self.labels())
        self.cypher(f"MATCH (this_set:{this_set_labels}{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(this_set_item:AbstractStructItem) "
                    "WITH this_set,COLLECT(this_set_item.hash_value) AS this_set_hash_nums "
                    f"MATCH (other_set:{other_set_labels}{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(other_set_item:AbstractStructItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value_node) "
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
        new_set = self.__class__().save()
        this_set_name = self.name
        other_set_name = other.name
        new_set_name = new_set.name
        this_set_labels = ":".join(self.labels())
        other_set_labels = ":".join(other.labels())
        new_set_labels = ":".join(new_set.labels())
        self.cypher(f"MATCH (this_set:{this_set_labels}{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(an_element:AbstractStructItem:SetItem) WITH COLLECT(an_element.hash_value) as this_set_hash_values MATCH (other_set:{other_set_labels}{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(another_element:AbstractStructItem:SetItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_set_value) WHERE another_element.hash_value IN this_set_hash_values WITH another_element,a_set_value MATCH (new_set:{new_set_labels}{{name:'{new_set_name}'}}) CREATE (new_set)-[:SET_ELEMENT]->(:AbstractStructItem:SetItem{{hash_value:another_element.hash_value}})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_set_value)")
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
        other_set_labels = ":".join(other.labels())
        this_set_labels = ":".join(self.labels())
        new_set_labels = ":".join(new_set.labels())
        self.cypher(f"MATCH (other_set:{other_set_labels}{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(other_element:AbstractStructItem:SetItem) WITH COLLECT(other_element.hash_value) AS other_set_hash_values MATCH (this_set:{this_set_labels}{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(this_element:AbstractStructItem:SetItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value) WHERE NOT this_element.hash_value IN other_set_hash_values WITH this_element, a_value MATCH (new_set:{new_set_labels}{{name:'{new_set_name}'}}) CREATE (new_set)-[:SET_ELEMENT]->(:AbstractStructItem:SetItem{{hash_value:this_element.hash_value}})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value)")
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
        other_set_labels = ":".join(other.labels())
        this_set_labels = ":".join(self.labels())
        new_set_labels = ":".join(new_set.labels())

        # Symmetric difference implemented as two difference queries here (A-B)|(B-A)
        # A-B        
        self.cypher(f"MATCH (other_set:{other_set_labels}{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(other_element:AbstractStructItem:SetItem) WITH COLLECT(other_element.hash_value) AS other_set_hash_values MATCH (this_set:{this_set_labels}{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(this_element:AbstractStructItem:SetItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value) WHERE NOT this_element.hash_value IN other_set_hash_values WITH this_element, a_value MATCH (new_set:{new_set_labels}{{name:'{new_set_name}'}}) CREATE (new_set)-[:SET_ELEMENT]->(:AbstractStructItem:SetItem{{hash_value:this_element.hash_value}})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value)")

        other_set_name = self.name
        this_set_name = other.name

        # B-A
        self.cypher(f"MATCH (other_set:{other_set_labels}{{name:'{other_set_name}'}})-[:SET_ELEMENT]->(other_element:AbstractStructItem:SetItem) WITH COLLECT(other_element.hash_value) as other_set_hash_values MATCH (this_set:{this_set_labels}{{name:'{this_set_name}'}})-[:SET_ELEMENT]->(this_element:AbstractStructItem:SetItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value) WHERE NOT this_element.hash_value IN other_set_hash_values WITH this_element, a_value MATCH (new_set:{new_set_labels}{{name:'{new_set_name}'}}) CREATE (new_set)-[:SET_ELEMENT]->(:AbstractStructItem:SetItem{{hash_value:this_element.hash_value}})-[:ABSTRACT_STRUCT_ITEM_VALUE]->(a_value)")
        
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
        this_set_labels = ":".join(self.labels())
        itm_hash = a_hash

        # NOTE: Hash operations need '{itm_hash:x}' because hash is a string
        return len(self.cypher(f"MATCH (a_set:{this_set_labels}{{name:'{nme}'}})-[:SET_ELEMENT]->(an_element:SetItem) WHERE an_element.hash_value='{itm_hash:x}' RETURN an_element")[0]) > 0

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
            this_set_labels = ":".join(self.labels())
            itm_hash = a_hash
            return self.cypher(f"MATCH (a_set:{this_set_labels}{{name:'{nme}'}})-[:SET_ELEMENT]->(an_element:SetItem) WHERE an_element.hash_value='{itm_hash:x}' return an_element")[0][0]
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
            this_set_labels = ":".join(self.labels())
            itm_hash = a_hash
            self.cypher(f"MATCH (a_set:{this_set_labels}{{name:'{nme}'}})-[:SET_ELEMENT]->(an_element:SetItem) WHERE an_element.hash_value='{itm_hash:x}' DETACH DELETE an_element")
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
        this_set_labels = ":".join(self.labels())
        self._pre_action_check("clear")
        self.cypher(f"MATCH (a_set:{this_set_labels}{{name:'{nme}'}})-[r1:SET_ELEMENT]->(el_item:SetItem)-[r2:ABSTRACT_STRUCT_ITEM_VALUE]->() DETACH DELETE r2,el_item,r1")

    def destroy(self):
        """
        Clears the set and removes it from the DBMS completely.
        """
        self._pre_action_check("destroy")
        self.clear()
        self.delete()
