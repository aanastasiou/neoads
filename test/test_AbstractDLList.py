"""
Athanasios Anastasiou Sep 2018

Tests functionality that is specific to AbstractDLList and is not covered by the general tests described in
`test_DataTypeFeatures.py`.

"""
import random
import pytest
import neomodel
import neoads


def test_is_not_hashable():
    """
    AbstractDLList (itself) should NOT be hashable.
    """

    u = neoads.AbstractDLList().save()

    with pytest.raises(TypeError):
        u._neoads_hash()

    u.destroy()


# TODO: HIGH, The __len__ operator should be generalised and added to the `test_DataTypeFeatures.py` tests.
def test_len():
    """
    AbstractDLList should return its length.
    """

    # Create some generic content that is to be added to the DLList by query
    elements = [neoads.SimpleNumber(random.random()).save() for i in range(0, 10)]
    # # Create and populate the DLList
    u = neoads.AbstractDLList().save()
    [u.append(an_element) for an_element in elements]
    # u.from_query("MATCH (ListItem:SimpleNumber) WHERE ListItem.name IN [{lmn_name}]"
    #              .format(lmn_name=",".join(element_names)))
    # Run the test
    assert len(u) == len(elements)
    # Clean up
    u.destroy()
    [an_item.delete() for an_item in elements]


# TODO: HIGH, The __len__ operator should be generalised and added to the `test_DataTypeFeatures.py` tests.
def test_delitem():
    """
    AbstractDLList should be capable of erasing an element from any position in the list with plain Python like del u[5]
    """
    # Create some generic content that is to be added to the DLList by query
    elements = [neoads.SimpleNumber(random.random()).save() for i in range(0, 10)]
    # # Create and populate the DLList
    u = neoads.AbstractDLList().save()
    [u.append(an_element) for an_element in elements]
    # Delete an item at random
    item_to_delete = random.randint(0,len(u)-1)
    del(u[item_to_delete])
    # Run the test
    assert len(u) == len(elements)-1
    # Clean up
    u.destroy()
    [an_item.delete() for an_item in elements]


def test_extend_by_merging():
    """
    AbstractDLList should extend itself by another AbstractDLList
    """
    # TODO: HIGH, This test does not cover the cases where given two lists u,v with v to be merged on to u, either of
    #       the lists are emtpy. Must add these two test cases.
    # Create some generic content that is to be added to the DLLists by query
    elements = [neoads.SimpleNumber(random.random()).save() for i in range(0, 4)]
    # # Create and populate the DLLists
    u = neoads.AbstractDLList().save()
    v = neoads.AbstractDLList().save()
    v_list_name = v.name
    [u.append(an_element) for an_element in elements[0:2]]
    [v.append(an_element) for an_element in elements[2:4]]
    # Merge v into u
    u.extend_by_merging(v)
    # After the merge, list v should not exist
    with pytest.raises(neomodel.exceptions.DoesNotExist):
        m = neoads.AbstractDLList.nodes.get(name=v_list_name)
    assert len(u) == len(elements)
    # Clean up
    u.destroy()
    [an_item.delete() for an_item in elements]


def test_from_query():
    """
    AbstractDLList should be capable of initialising from a special **INCOMPLETE** READ CYPHER Query.
    """
    # Create some generic content that is to be added to the DLList by query
    elements = [neoads.SimpleNumber(random.random()).save() for i in range(0, 10)]
    element_names = ["'{}'".format(an_element.name) for an_element in elements]
    # Create and populate the DLList
    u = neoads.AbstractDLList().save()
    u.from_query("MATCH (ListItem:SimpleNumber) WHERE ListItem.name IN [{lmn_name}]"
                 .format(lmn_name=",".join(element_names)))
    # Run the test
    assert len(u) == len(elements)
    # Clean up
    u.destroy()
    [an_item.delete() for an_item in elements]


def test_from_id_array():
    """
    AbstractDLList should be capable of initialising from a CompositeArrayNumber that contains IDs
    """
    # Create some generic content that is to be added to the DLList by query
    elements = [neoads.SimpleNumber(random.random()).save() for i in range(0, 10)]
    element_names = ["'{}'".format(an_element.name) for an_element in elements]
    # Create the CompositeNumber array from a query
    v = neoads.CompositeArrayNumber([]).save()
    v.from_query_IDs("MATCH (ListItem:SimpleNumber) WHERE ListItem.name IN [{}] ".format(",".join(element_names)))
    # We now have the CompositeArrayNumber we need, let's create the AbstractDLList.
    u = neoads.AbstractDLList().save()
    # Now populate from the array
    u.from_id_array(v)
    # Run the test
    assert len(u) == len(elements)
    # Clean up
    u.destroy()
    v.delete()
    [an_item.delete() for an_item in elements]