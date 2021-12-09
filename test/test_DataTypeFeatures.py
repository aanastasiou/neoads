"""
    Athanasios Anastasiou Mar 2019

    Universal abstract data object features, mostly applicable to Simple data type variables.
"""

import random
import hashlib
import datetime
import neomodel
import pytest
from neoads import *


@pytest.mark.parametrize("ads_class_requiring_default_value", [SimpleNumber, SimpleDate, CompositeString,
                                                              CompositeArrayNumber, CompositeArrayString,
                                                              CompositeArrayDate])
def test_fail_init_without_default_value(ads_class_requiring_default_value):
    """
    Tests for successful variable initialisation WITH a default value.

    NOTE:
        In the majority of structures currently covered by neoads, this test should be passed by Simple and Composite
        data types.

    :param ads_class_requiring_default_value:
    :type ads_class_requiring_default_value:
    """

    with pytest.raises(TypeError) as e:
        u = ads_class_requiring_default_value().save()
    assert "required positional argument: 'value'" in str(e.value)


@pytest.mark.parametrize("ads_class_not_requiring_default_value", [AbstractSet, AbstractMap, AbstractDLList])
def test_pass_init_without_default_value(ads_class_not_requiring_default_value):
    """
    Tests for successful variable initialisation WITHOUT a default value.

    NOTE:
        These are mostly the abstract data types (Set, Map, Doubly Linked List)

    :param ads_class_not_requiring_default_value:
    :type ads_class_not_requiring_default_value:
    """

    u = ads_class_not_requiring_default_value().save()
    v = ads_class_not_requiring_default_value.nodes.get(name=u.name)

    assert type(v) is ads_class_not_requiring_default_value

    u.destroy()


@pytest.mark.parametrize("ads_class, ads_class_invalid_value", [(SimpleNumber, "Not int or float"),
                                                                (SimpleDate, "Not a date"),
                                                                (CompositeString, 0),
                                                                (CompositeArrayNumber, 1),
                                                                (CompositeArrayDate, "Not a date"),
                                                                (CompositeArrayString, 12)])
def test_fail_simple_value_validation(ads_class, ads_class_invalid_value):
    """
    Tests for unsuccessful initialisation with an INVALID value.

    :param ads_class:
    :param ads_class_invalid_value:
    """
    # NOTE: Originally, these problems with initialisation were caught via neomodel's DeflateError. However, after
    #       #429 (https://github.com/neo4j-contrib/neomodel/issues/429), the TypeError exception was added. In the
    #       long term, these should really be caught as early as possible (FOR ALL TYPES), most likely via TypeError.
    with pytest.raises((neomodel.exceptions.DeflateError, TypeError)):
        ads_class(ads_class_invalid_value).save()


@pytest.mark.parametrize("ads_class, ads_class_valid_value, ads_class_returned_value_type",
                         [(SimpleNumber, 3.1415928, float),
                          (SimpleNumber, 42, float),
                          (SimpleDate, datetime.date(1938, 10, 1), datetime.date),
                          (CompositeString, "The quick brown fox jumps over the "
                                            "lazy dog", str),
                          (CompositeArrayNumber, [1, 2, 3], list),
                          (CompositeArrayNumber, [3.1415928, 1.618033], list),
                          (CompositeArrayDate, [datetime.date(1938, 10, 1),
                                                datetime.date(1873, 9, 13)], list),
                          (CompositeArrayString, ["Alpha", "Beta", "Gamma"], list),
                          ])
def test_pass_simple_value_validation(ads_class, ads_class_valid_value, ads_class_returned_value_type):
    """
    Tests for successful initialisation with a VALID value.

    :param ads_class:
    :param ads_class_valid_value:
    :param ads_class_returned_value_type:
    """
    # NOTE: It is useful to note here the way SimpleNumber is validated because it uses the same data type to store
    #       Integer or Real numbers. In both cases, the returned data type should be float, irrespectively of how
    #       the input was presented to the data type.

    u = ads_class(ads_class_valid_value).save()
    v = ads_class.nodes.get(name=u.name)

    assert type(v) is ads_class
    assert isinstance(v.value, ads_class_returned_value_type)
    assert v.value == ads_class_valid_value

    u.delete()


@pytest.mark.parametrize("ads_class, ads_class_valid_value",
                         [(SimpleNumber, 3.1415928),
                          (SimpleDate, datetime.date(1938, 10, 1)),
                          (CompositeString, "The quick brown fox jumps over the lazy dog"),
                          ])
def test_hash(ads_class, ads_class_valid_value):
    """
    Tests the return value of the hash function. For neoads, that is _neoads_hash()

    NOTE:
        Data types that are supposed to be used as keys in mappings or as elements of sets should provide a valid
        hash function. If two variables produce the same hash, they are assumed to point to the same value.
    """
    value_hash = int(hashlib.sha256(str(ads_class_valid_value).encode("utf-8")).hexdigest(), base=16)
    u = ads_class(ads_class_valid_value).save()
    v = ads_class.nodes.get(name=u.name)
    assert v._neoads_hash() == value_hash
    u.delete()


# TODO: HIGH, The length test must become generic so that it allows Abstracts to be tested too. Maybe pass a function
#       that initialises the variable and run the tests on that one rather than passing the class itself, or, create
#       an alternative constructor that could handle initialisation via an iterable of objects.
@pytest.mark.parametrize("ads_class, ads_class_valid_value",
                         [(CompositeString, "The quick brown fox jumps over the lazy dog"),
                          (CompositeArrayNumber, [3.1415928, 1.618033]),
                          (CompositeArrayDate, [datetime.date(1938, 10, 1),
                                                datetime.date(1873, 9, 13)]),
                          (CompositeArrayString, ["Alpha", "Beta", "Gamma"]),
                          ])
def test_length(ads_class, ads_class_valid_value):
    """
    Tests the __len__ function for entities that implement it (e.g. CompositeArray).

    :param ads_class:
    :param ads_class_valid_value:
    :param ads_class_value_len:
    """
    value_len = len(ads_class_valid_value)
    u = ads_class(ads_class_valid_value).save()
    v = ads_class.nodes.get(name=u.name)
    v_len = len(v)
    assert value_len == v_len
    u.delete()


@pytest.mark.parametrize("ads_class, ads_class_valid_value",
                         [(CompositeString, "The quick brown fox jumps over the lazy dog"),
                          (CompositeArrayNumber, [3.1415928, 1.618033]),
                          (CompositeArrayDate, [datetime.date(1938, 10, 1),
                                                datetime.date(1873, 9, 13)]),
                          (CompositeArrayString, ["Alpha", "Beta", "Gamma"]),
                          ])
def test_pass_valid_key_get(ads_class, ads_class_valid_value):
    """
    Tests that __getitem__(key) retrieves the right element when key is valid wherever __getitem__(key) is implemented.

    :param ads_class:
    :param ads_class_valid_value:
    """

    # Create a variable
    u = ads_class(ads_class_valid_value).save()
    # Select a random element to return
    n = random.randint(0, len(ads_class_valid_value)-1)
    # Run the test
    assert u[n] == ads_class_valid_value[n]
    # Get rid of the node
    u.delete()

@pytest.mark.parametrize("ads_class, ads_class_valid_value",
                         [(CompositeString, "The quick brown fox jumps over the lazy dog"),
                          (CompositeArrayNumber, [3.1415928, 1.618033]),
                          (CompositeArrayDate, [datetime.date(1938, 10, 1),
                                                datetime.date(1873, 9, 13)]),
                          (CompositeArrayString, ["Alpha", "Beta", "Gamma"]),
                          ])
def test_fail_invalid_key_get(ads_class, ads_class_valid_value):
    """
    Tests that __getitem__(key) fails with an appropriate exception when key is invalid wherever __getitem__(key) is
    implemented.

    :param ads_class:
    :param ads_class_valid_value:
    """
    # Create a variable
    u = ads_class(ads_class_valid_value).save()
    # Select an element from an invalid key
    n = len(ads_class_valid_value) + 8
    # Run the test
    with pytest.raises(IndexError):
        v = u[n]
    # Get rid of the node
    u.delete()


@pytest.mark.parametrize("ads_class, ads_class_valid_value, key_to_set, value_to_set",
                         [(CompositeArrayNumber, [3.1415928, 1.618033], 1, 0.33333333),
                          (CompositeArrayDate, [datetime.date(1938, 10, 1), datetime.date(1873, 9, 13)], 1,
                           datetime.date(1908, 1, 15)),
                          (CompositeArrayString, ["Alpha", "Beta", "Gamma"], 2, "Testing"),
                          ])
def test_pass_valid_key_set(ads_class, ads_class_valid_value, key_to_set, value_to_set):
    """
    Tests that __setitem__(key, value) resets value when key is valid wherever __setitem__(key, value) is implemented.

    :param ads_class:
    :param ads_class_valid_value:
    :param key_to_set:
    :param value_to_set:
    """
    # Create a variable
    u = ads_class(ads_class_valid_value).save()
    # Set the element
    u[key_to_set] = value_to_set
    # Run the test
    assert u[key_to_set] == value_to_set
    assert type(u[key_to_set]) is type(value_to_set)
    # Get rid of the node
    u.delete()


@pytest.mark.parametrize("ads_class, ads_class_valid_value",
                         [(CompositeArrayNumber, [3.1415928, 1.618033]),
                          (CompositeArrayDate, [datetime.date(1938, 10, 1), datetime.date(1873, 9, 13)]),
                          (CompositeArrayString, ["Alpha", "Beta", "Gamma"]),
                          ])
def test_fail_invalid_key_set(ads_class, ads_class_valid_value):
    """
    Tests that __setitem__(key, value) resets value when key is valid wherever __setitem__(key, value) is implemented.

    :param ads_class:
    :param ads_class_valid_value:
    :param key_to_set:
    :param value_to_set:
    """
    # Create a variable
    u = ads_class(ads_class_valid_value).save()
    # Try to reset using an absurd key, this should now fail
    with pytest.raises(IndexError):
        u[len(ads_class_valid_value)+12] = u[0]

    # Get rid of the node
    u.delete()
