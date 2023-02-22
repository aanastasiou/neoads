"""
Tests functionality that is specific to AbstractMap and is not covered by the general tests described in
`test_DataTypeFeatures.py`.

:author: Athanasios Anastasiou
:date: Sep 2018
"""
import pytest
import neoads


def test_is_not_hashable():
    """
    AbstractMap (itself) should NOT be hashable.
    """

    u = neoads.AbstractMap().save()

    with pytest.raises(TypeError):
        u._neoads_hash()

    u.destroy()


# TODO: HIGH, The __contains__ operators should be generalised and be added to `test_DataTypeFeatures.py` as generic
#       tests.
def test_operator_in():
    """
    Tests that the __contains__() operator works as expected when applied to AbstractMap
    """

    # Create some generic content that is to be added to the Set
    data = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0}
    elements = [(neoads.CompositeString(an_item[0]).save(), neoads.SimpleNumber(an_item[1]).save())
                for an_item in data.items()]
    # # Create and populate the map
    u = neoads.AbstractMap().save()
    for an_item in elements:
        u[an_item[0]] = an_item[1]

    # # Perform the test
    assert elements[0][0] in u and \
        elements[1][0] in u and \
        elements[2][0] in u and \
        elements[2][0] in u

    # Get rid of the nodes that were created for this test
    u.destroy()
    [(an_item[0].delete(), an_item[1].delete()) for an_item in elements]


# TODO: HIGH, The __len__ operator should be generalised and added to the `test_DataTypeFeatures.py` tests.
def test_len():
    """
    AbstractMap should return its length.
    """

    # Create some generic content that is to be added to the Set
    data = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0}
    elements = [(neoads.CompositeString(an_item[0]).save(), neoads.SimpleNumber(an_item[1]).save())
                for an_item in data.items()]
    # # Create and populate the map
    u = neoads.AbstractMap().save()
    for an_item in elements:
        u[an_item[0]] = an_item[1]
    # Run the test
    assert len(u) == 4

    # Clean up
    u.destroy()
    [(an_item[0].delete(), an_item[1].delete()) for an_item in elements]


# TODO: HIGH, The __len__ operator should be generalised and added to the `test_DataTypeFeatures.py` tests.
def test_delitem():
    """
    It should be possible to delete any element of an AbstractMap with plain Python like del u[1]
    """
    # Create some generic content that is to be added to the Set
    data = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0}
    elements = [(neoads.CompositeString(an_item[0]).save(), neoads.SimpleNumber(an_item[1]).save())
                for an_item in data.items()]
    # # Create and populate the map
    u = neoads.AbstractMap().save()
    for an_item in elements:
        u[an_item[0]] = an_item[1]
    # Run the test
    del u[elements[0][0]]
    assert elements[0][0] not in u
    # Clean up
    u.destroy()
    [(an_item[0].delete(), an_item[1].delete()) for an_item in elements]


def test_from_keyvalue_node_query():
    """
    An AbstractMap can be instantiated via a query with a specific structure.
    """
    # Create some generic content that is to be added to the Set
    data = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0}
    elements = [(neoads.CompositeString(an_item[0]).save(), neoads.SimpleNumber(an_item[1]).save())
                for an_item in data.items()]
    # This is required here to make sure that we are operating on the right elements.
    element_names = []
    for an_element in elements:
        element_names.append(f"'{an_element[0].name}'")
        element_names.append(f"'{an_element[1].name}'")
    # Create the map
    you = neoads.AbstractMap().save()

    lmn_names=",".join(element_names)

    # Populate the map via a query
    you.from_keyvalue_node_query(f"MATCH (a:CompositeString) WHERE a.value IN ['One', 'Two', 'Three', 'Four'] AND "
                                 f"a.name IN [{lmn_names}] "
                                 "WITH collect(a) AS Keys "
                                 f"MATCH (b:SimpleNumber) WHERE b.value IN [1, 2, 3, 4] AND b.name IN [{lmn_names}] "
                                 "WITH Keys, collect(b) AS Values RETURN Keys, Values")
    # Run the test
    assert len(you) == 4
    assert elements[0][0] in you
    # Clean up
    you.destroy()
    [(an_item[0].delete(), an_item[1].delete()) for an_item in elements]
