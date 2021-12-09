"""
Athanasios Anastasiou Mar 2019

Runs basic tests for the memory manager object.
"""

import random
import neomodel
from neoads import MemoryManager, CompositeString


def test_list_objects():
    """
    Tests if MemoryManager's equivalent of `dir()` operates as expected.
    """

    some_data = [CompositeString(str(random.randint(0, 10000))).save() for i in range(0, 10)]
    # At this point a neomodel.db object has already been prepared by conftest.py. Just initialise a memory manager from
    # that object
    mm = MemoryManager(connection_uri=neomodel.db.url)
    objects_in_mem = mm.list_objects()

    # Run the test
    assert len(objects_in_mem) == len(some_data)

    # Clean up
    [an_item.delete() for an_item in some_data]


def test_get_object():
    """
    MemoryManager should return reference to an object by name.
    """
    some_data = [CompositeString(str(random.randint(0, 10000))).save() for i in range(0, 10)]
    mm = MemoryManager(connection_uri=neomodel.db.url)
    # Request some random object from the list
    some_random_n = random.randint(0,len(some_data)-1)
    some_object = mm.get_object(some_data[some_random_n].name)
    # Run the test
    assert type(some_object) is type(some_data[some_random_n])
    # TODO: MED, Revise this test, it can only be carried out between hashable entities.
    assert some_object._neoads_hash() == some_data[some_random_n]._neoads_hash()

    # Clean up
    [an_item.delete() for an_item in some_data]
