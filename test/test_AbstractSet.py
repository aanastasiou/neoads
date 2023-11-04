"""
Tests functionality that is specific to AbstractSet and is not covered by the general tests described in
`test_DataTypeFeatures.py`

:author: Athanasios Anastasiou
:date: Sep 2018
"""
import random
import pytest
import neoads


def test_logic_operators():
    """
    Tests that logic operators such as union, intersection, difference and symmetric difference, work as expected.

    NOTE:
         All operators are tested in this one test here by unrolling the symmetric difference over two sets.
    """

    # The test is based on the following equivalence
    # U = {1,2,3}
    # V = {2,3,6,5}
    # (U-V)|(V-U) == U^V

    # Create some generic content for the sets
    n1 = neoads.SimpleNumber(1).save()
    n2 = neoads.SimpleNumber(2).save()
    n3 = neoads.SimpleNumber(3).save()
    n5 = neoads.SimpleNumber(5).save()
    n6 = neoads.SimpleNumber(6).save()

    # Create and populate the required sets
    U = neoads.AbstractSet().save()
    V = neoads.AbstractSet().save()
    U.add(n1).add(n2).add(n3)
    V.add(n2).add(n3).add(n5).add(n6)

    # Run the test
    # The symmetric difference could also have been obtained in one line but the intermediate sets would be inaccessible
    # to the test and would have to be garbage collected later on. Instead, the intermediate tests are obtained here
    # and therefore can be deleted in the end.
    umv = U - V
    vmu = V - U
    umv_or_vmu = umv | vmu
    uv_symdiff = U ^ V
    # This test tests all of the operators EXCEPT for intersection.
    assert umv_or_vmu == uv_symdiff
    # Test the intersection operator
    u_and_v = U & V
    assert len(u_and_v) == 2 and \
        n2 in u_and_v and \
        n3 in u_and_v

    # Get rid of nodes that were created during this test
    U.destroy()
    V.destroy()
    umv.destroy()
    vmu.destroy()
    umv_or_vmu.destroy()
    uv_symdiff.destroy()
    u_and_v.destroy()
    n1.delete()
    n2.delete()
    n3.delete()
    n5.delete()
    n6.delete()


# TODO: HIGH, The __contains__ operators should be generalised and be added to `test_DataTypeFeatures.py` as generic
#       tests.
def test_operator_in():
    """
    Tests that the __contains__() operator works as expected when applied to AbstractSet
    """

    # Create some generic content that is to be added to the Set
    some_numbers = [neoads.SimpleNumber(a_number).save() for a_number in range(0,4)]
    some_random_number = neoads.SimpleNumber(120).save()
    # Create and populate the set of numbers
    some_set = neoads.AbstractSet().save()
    [some_set.add(a_number) for a_number in some_numbers]
    # Perform the test
    assert some_numbers[random.randint(0, len(some_numbers)-1)] in some_set, "AbstractSet.__contains__() failed"
    assert some_random_number not in some_set, "AbstractSet.__contains__() failed."
    # Get rid of the nodes that were created for this test
    some_set.destroy()
    some_random_number.delete()
    [a_number.delete() for a_number in some_numbers]


def test_from_abstractset():
    """
    Tests the copy-constructor function `from_abstractset`.
    """

    # Create some generic content that is to be added to the Set
    some_numbers = [neoads.SimpleNumber(a_number).save() for a_number in range(0,4)]
    # Create and populate the set of numbers
    some_set = neoads.AbstractSet().save()
    [some_set.add(a_number) for a_number in some_numbers]
    # Create another set that is empty
    another_set = neoads.AbstractSet().save()
    # Initialise it
    another_set.from_abstractset(some_set, auto_reset=True)
    # Make sure that it contains what it is supposed to contain
    assert len(another_set) == len(some_set), "from_abstractset() produced set of invalid length"
    assert some_numbers[0] in another_set and \
        some_numbers[1] in another_set and \
        some_numbers[2] in another_set and \
        some_numbers[3] in another_set, "from_abstractset() produced set with invalid contents"

    # Get rid of the nodes that were created for this test
    another_set.destroy()
    some_set.destroy()
    [a_number.delete() for a_number in some_numbers]


def test_add():
    """
    AbstractSet should store and recall ANY PersistentElement type variables.

    NOTE:
        This is tested here using ANY ElementVariable.
    """

    s1 = neoads.CompositeString("Alpha").save()
    s2 = neoads.CompositeString("Beta").save()
    s3 = neoads.CompositeString("Gamma").save()
    s4 = neoads.CompositeString("Gamma").save()

    u = neoads.AbstractSet().save()
    u.add(s1).add(s2).add(s3).add(s4)

    v = neoads.AbstractSet.nodes.get(name=u.name)

    assert type(v) is neoads.AbstractSet
    assert len(v) == 3
    assert s1 in v and s2 in v and s3 in v

    u.destroy()
    s1.delete()
    s2.delete()
    s3.delete()
    s4.delete()


def test_is_not_hashable():
    """
    AbstractSet (itself) should NOT be hashable
    """

    u = neoads.AbstractSet().save()

    with pytest.raises(TypeError):
        u._neoads_hash()

    u.destroy()


# TODO: HIGH, The __len__ operator should be generalised and added to the `test_DataTypeFeatures.py` tests.
def test_len():
    """
    AbstractSet should return its length.
    """

    # Create some generic content
    s1 = neoads.CompositeString("Alpha").save()
    s2 = neoads.CompositeString("Beta").save()
    s3 = neoads.CompositeString("Gamma").save()

    # Populate the set
    u = neoads.AbstractSet().save()
    u.add(s1).add(s2).add(s3)

    v = neoads.AbstractSet.nodes.get(name=u.name)
    # Run the test
    assert len(v) == 3

    # Clean up
    u.destroy()
    s1.delete()
    s2.delete()
    s3.delete()

def test_from_query():
    """
    AbstractSet can be constructed server-side via queries
    """

    # Create some generic content
    s1 = neoads.CompositeString("Alpha").save()
    s2 = neoads.CompositeString("Beta").save()
    s3 = neoads.CompositeString("Gamma").save()
    s4 = neoads.CompositeString("Alpha").save()

    # Populate the set via a query
    u = neoads.AbstractSet().save()
    u.from_query("MATCH (SetItem:CompositeString)")
    assert 1
    # Clean up
    # u.destroy()
    # s1.delete()
    # s2.delete()
    # s3.delete()
