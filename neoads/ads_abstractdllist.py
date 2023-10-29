"""
Definitions for the abstract double linked list (``AbstractDLList``).

An ``AbstractDLList`` is represented in Neo4j with the following object diagram:

.. graphviz::

    digraph foo {
        graph [
            rankdir=LR
        ]
        node [
              shape=record
             ]

        ADS_DLList [
            label = "{{a:AbstractDLList|+head|+name}}"
            ]

        ADS_DLListItem1 [
            label="{{b:DLListItem|nxt|prv|value}}"
        ]

        ADS_ElementDomain1 [
            label="{{c:PersistentElement|}}"
        ]

        ADS_DLListItem2 [
            label="{{d:DLListItem|nxt|prv|value}}"
        ]

        ADS_ElementDomain2 [
            label="{{e:PersistentElement|}}"
        ]
        
        ADS_DLList -> ADS_DLListItem1 [label="DLL_NXT"]
        ADS_DLListItem1 -> ADS_DLListItem2 [label="DLL_NXT"]
        ADS_DLListItem2 -> ADS_DLListItem1 [label="DLL_PRV"]
        ADS_DLListItem1 -> ADS_ElementDomain1 [label="ABSTRACT_STRUCT_ITEM_VALUE"]
        ADS_DLListItem2 -> ADS_ElementDomain2 [label="ABSTRACT_STRUCT_ITEM_VALUE"]
    }


* This diagram shows a double linked list with two elements.

* Where ``PersistentElement`` can be **ANY** entity in the data model deriving from ``PersistentElement``.

* The module defines both end-user data structures as well as intermediate (or helper) data structures.


For more details please see :ref:`datamodeling` 



:author: Athanasios Anastasiou 
:date: Jan 2018

"""

import neomodel
from .core import PersistentElement
from .composite_array import CompositeArrayNumber
from . import exception
from .ads_core import AbstractStructItem, CompositeAbstract


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

    .. note::

        Although the list is Doubly Linked, only the list's ``head`` is preserved with the List entry.

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

        .. note::

            To delete the list itself, use destroy()

        """
        self._pre_action_check('clear')
        nme = self.name
        this_list_labels = ":".join(self.labels())
        # TODO; HIGH, Turn static labels to dynamic ones
        self.cypher(f"MATCH (a_list:{this_list_labels}{{name:'{nme}'}})-[:DLL_NXT*]-(data_item:DLListItem) DETACH DELETE data_item")
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

        .. note::

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

        .. note::

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
            this_list_labels = ":".join(self.labels())
            listIdentifier = this_list_known_as
            projectedField = projected_field
            projectionKnownAs = projection_known_as

            # TODO; HIGH, Turn static labels to dynamic ones
            item_query = f"MATCH ({listIdentifier}:{this_list_labels}{{name:'{nme}'}}) WITH {listIdentifier} MATCH ({listIdentifier})-[:DLL_NXT*]->({listIdentifier}_listItem:DLListItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->({listIdentifier}_listItemValue) WITH collect(id({listIdentifier}_listItemValue)) as {projectionKnownAs}  "
        else:
            # TODO; HIGH, Turn static labels to dynamic ones
            item_query = "MATCH ({listIdentifier}:{this_list_labels}{{name:'{nme}'}}) WITH {listIdentifier} MATCH ({listIdentifier})-[:DLL_NXT*]->({listIdentifier}_listItem:DLListItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->({listIdentifier}_listItemValue) WITH collect({listIdentifier}_listItemValue.{projectedField}) as {projectionKnownAs}  "
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
        this_list_labels =  ":".join(labels())
        list_known_as = this_list_known_as
        other_lists = ",{','.join(other_lists) if other_lists is not None else ''}"

        # TODO: HIGH, Propagate the lists correctly.
        return f"MATCH (aList:{this_list_labels}{{name:'{nme}'}}) WITH aList{other_lists} MATCH (aList)-[:DLL_NXT*]->(:DLListItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(aList_listItemValue) WITH collect(aList_listItemValue) AS {list_known_as}{other_lists}"

    def iterate_by_query(self, this_list_known_as):
        """
        Generates a query that iterates over all items of the list.

        .. note::

            This can be used to "trigger" further queries / operations over each item within the list.


        .. warning::

            These are the ACTUAL ITEMS that the list is holding. If this list is pointing to other lists, those
            lists are not automatically UNWINDED!!!!


        **EXAMPLE:**

        ::

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
        this_list_labels = ":".join(self.labels())
        return f"MATCH ({listIdentifier}:{this_list_labels}{{name:'{self.name}'}}) WITH {this_list_known_as} MATCH ({this_list_known_as})-[:DLL_NXT*]->({this_list_known_as}_listItem:DLListItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->({this_list_known_as}_listItemValue) WITH {this_list_known_as}_listItemValue "

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
            this_list_labels = ":".join(self.labels())
            this_list_tail_item = DLListItem.inflate(self.cypher(f"MATCH (a_list:{this_list_labels}{{name:'{self.name}'}})-[:DLL_NXT*]-(data_item:DLListItem) WHERE NOT (data_item)-[:DLL_NXT]->() RETURN data_item")[0][0][0])
            # Retrieve the head STRUCT item of the other list.
            # The head item is readily available
            other_list_head_item = other_list.head[0]
            # Effect the concatenation
            this_list_tail_item.nxt.connect(other_list_head_item)
            other_list_head_item.prv.connect(this_list_tail_item)
            # Adjust the length of this list.
            self.length += other_list.length
            # Delete the **ENTRY** of the other list
            other_list_labels = ":".join(other_list.labels())
            other_list.cypher(f"MATCH (a:{other_list_labels}{{name:'{other_list.name}'}}) "
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
                other_list_labels = ":".join(other_list.labels())
                other_list.cypher(f"MATCH (a:{other_list_labels}{{name:'{other_list.name}'}}) "
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
            this_list_labels = ":".join(self.labels())
            this_list_tail_item = DLListItem.inflate(self.cypher(f"MATCH (a_list:{this_list_labels}{{name:'{self.name}'}})-[:DLL_NXT*]-(data_item:DLListItem) "
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

        .. note::

            The list's items point to the return result of ``query``. The query **MUST** return ``PersistentElement`` and be
            a CYPHER READ query.

        .. warning::

            At the moment, the way the CYPHER queries that build the list are expressed, they seem to "explode" with
            the number of items returned by from_query(..., query). So use with caution.

            If the query returns duplicates, these are retained in the list because a list does not behave like a set.

         **EXAMPLE:**

         ::

            "MATCH (ListItem:Institute)-[:CITY]-(:City)-[:IN_COUNTRY]-(:Country{countryName:'Australia'})"
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
        this_list_labels = ":".join(self.labels())
        self.cypher(f"MATCH (a_list:{this_list_labels}{{name:'{self.name}'}}) SET a_list.length=0")
        # Create list items and index them sequentially
        #.format(**{"nme" : self.name,"match_query":query,"dup_removal":dprem_query_fragment[no_duplicates]})
        nme = self.name
        match_query = query
        dup_removal = dprem_query_fragment[no_duplicates]

        # TODO: HIGH, if match_query contains WITH it must be ensured that aList is propagated in that query, otherwise this would fail (see also from_id_array)
        self.cypher(f"MATCH (a_list:{this_list_labels}{{name:'{nme}'}}) WITH a_list {match_query} WITH a_list, ListItem{dup_removal} CREATE (a_list)-[:TEMP_LINK{{of_list:a_list.name,item_id:a_list.length}}]->(an_item:DLListItem:AbstractStructItem)-[:ABSTRACT_STRUCT_ITEM_VALUE]->(ListItem) SET a_list.length=a_list.length+1")
        import pdb
        pdb.set_trace()
        
        # Create the double linked list connections
        # Create forwards connections
        self.cypher(f"MATCH (a_list:{this_list_labels}{{name:'{self.name}'}})-[r1:TEMP_LINK{{of_list:a_list.name}}]->(this_item:DLListItem:AbstractStructItem) WHERE r1.item_id<a_list.length WITH a_list,r1,this_item MATCH (a_list)-[r2:TEMP_LINK{{of_list:a_list.name}}]->(next_item:DLListItem:AbstractStructItem) WHERE r2.item_id=r1.item_id+1 CREATE (this_item)-[:DLL_NXT]->(next_item)")

        # Create backwards connections
        self.cypher(f"MATCH (a_list:{this_list_labels}{{name:'{self.name}'}})-[r1:TEMP_LINK{{of_list:a_list.name}}]->(this_item:DLListItem:AbstractStructItem) WHERE r1.item_id>0 WITH a_list,r1,this_item MATCH (a_list)-[r2:TEMP_LINK{{of_list:a_list.name}}]->(previous_item:DLListItem:AbstractStructItem) WHERE r2.item_id=r1.item_id-1 CREATE (this_item)-[:DLL_PRV]->(previous_item)")
        
        import pdb
        pdb.set_trace()
        
        # Connect the items to the head of the list
        self.cypher(f"MATCH (a_list:{this_list_labels}{{name:'{self.name}'}})-[r:TEMP_LINK{{of_list:a_list.name,item_id:0}}]->(a_list_item:DLListItem) WITH a_list,a_list_item CREATE (a_list)-[:DLL_NXT]->(a_list_item)")

        import pdb
        pdb.set_trace()
        
        # Delete the temporary links
        self.cypher(f"MATCH (a_list:{this_list_labels}{{name:'{self.name}'}})-[r:TEMP_LINK{{of_list:a_list.name}}]->(:DLListItem) DELETE r")
        # Now, length has changed, so this entity needs to be refreshed
        self.refresh()
        return self

    def from_id_array(self, array_of_ids, auto_reset=False):
        """
        Initialises the doubly linked list from a numeric array of node IDs.

        .. note::

            This array_of_ids is usually constructed via a call to ``CompositeArrayNumber.from_query_IDs()``.
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
