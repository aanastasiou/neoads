"""
Definitions for the abstract set (``AbstractSet``) data structure.

An ``AbstractMap`` is represented in Neo4j as follows:

.. graphviz::

    digraph foo {
        graph [
            rankdir=LR
        ]
        node [
              shape=record
             ]

        ADS_Map [
            label = "{{a:AbstractMap|+name}}"
            ]

        ADS_KeySet [
            label="{{b:AbstractSet|}}"
        ]

        ADS_ValuesSet [
            label="{{c:AbstractSet|}}"
        ]

        ADS_Map -> ADS_KeySet [label=KEYS_SET]
        ADS_Map -> ADS_ValuesSet [label=VALUES_SET]

    }

* Where ``AbstractSet`` is expanded as depicted `here <http://localhost:8000/api_abstractdatatypes.html#module-neoads.ads_abstractset>`_



:author: Athanasios Anastasiou 
:date: Jan 2018

"""

import neomodel
from .core import PersistentElement
from . import exception
from .ads_abstractset import SetItem, AbstractSet
from .ads_core import CompositeAbstract



# TODO: MED, Also needs initialisation by two existing AbstractSets, which could help with the recovery of stray
#            elements.
class AbstractMap(CompositeAbstract):
    """
    A very simple mapping that maps a hash value (that can be computed by any hashable) to an entity.

    .. note::

        The abstract map is implemented via two ``neoads.AbstractSets``, one for the keys and one for the values.
    """

    keys_set = neomodel.RelationshipTo("AbstractSet", "KEYS_SET", cardinality=neomodel.One)
    values_set = neomodel.RelationshipTo("AbstractSet", "VALUES_SET",cardinality=neomodel.One)

    @property
    def keys(self):
        """
        Return an iterator to keys.

        :returns: An iterator to the neoads elements that make up the `AbstractSet` of keys.
        :rtype: list
        """
        try:
            return map(lambda x:x.value[0], self.keys_set[0].elements.all())
        except IndexError:
            return None

    @property
    def values(self):
        """
        Return an iterator to values.

        :returns: An iterator to the neoads elements that make up the `AbstractSet` of values.
        :rtype: list
        """
        try:
            return map(lambda x:x.value[0], self.values_set[0].elements.all())
        except IndexError:
            return None

    def _init_map(self):
        """
        Initialises the map.

        .. note::

            Because of the way the object hierarchy is set up, an uninitialised set can exist without actual reference
            to the two ``AbstractSets`` it requires to function properly. **BUT**, when the time comes for the map to
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

        .. note::

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

        .. note::
            ``value`` should be a ``PersistentElement`` that has already been **saved** in the database.
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

        .. note::

            The query must have a specific structure and return two arrays, one for the keys and one for the values.
            For example:

            ::
                
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
            self.keys_set[0].from_hash_nodeid_list(list(zip(hash_values, [an_object.element_id for an_object in keyvalue_list[0][0][0]])), auto_reset=True)
            # Build the value set
            self.values_set[0].from_hash_nodeid_list(list(zip(hash_values, [an_object.element_id for an_object in keyvalue_list[0][1][0]])), auto_reset=True)
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
            key_set.destroy()
            value_set.destroy()
        except IndexError:
            pass
        # The key or value sets might not have been created yet in which case we just delete the map
        self.delete()

