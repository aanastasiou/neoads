"""
Athanasios Anastasiou Mar 2019

Tests functionality that is specific to CompositeArrayNumber and is not covered by the general tests described in
`test_DataTypeFeatures.py`
"""

from neoads import CompositeArrayNumber, SimpleNumber


def test_init_from_query_IDs():
    """
    Tests initialisation of a CompositeArrayNumber via its from_query_IDs() function.
    """

    # Setup some generic content first
    some_numbers = [SimpleNumber(an_item).save() for an_item in range(0, 10)]
    # Get the newly created numbers names. This has to be done here for two reasons:
    # 1. To demonstrate that the formation query can be arbitrarily complex
    # 2. If other tests running at the same time happen to create SimpleNumbers within the range
    #    specified by this test, this test will fail.
    number_variable_names = ",".join([f"'{a_number.name}'" for a_number in some_numbers])
    # Create the array itself. Here, an empty list is created.
    some_array = CompositeArrayNumber([]).save()
    # Populate the array with the IDs of specific nodes
    some_array.from_query_IDs("MATCH (ListItem:SimpleNumber) "
                              f"WHERE ListItem.name IN [{number_variable_names}] AND "
                              "ListItem.value>2 AND ListItem.value<8")
    # Now get a reference to the array
    # NOTE: This step is an extra failsafe for the test itself, it is not required in practice.
    u = CompositeArrayNumber.nodes.get(name=some_array.name)
    # Make sure that the contents match the original intention
    # There are 10 numbers in some_numbers, but only 5 of them within 2 < x < 8 (3,4,5,6,7)
    assert len(u) == 5, "CompositeArrayNumber.from_query_IDs() has returned incorrect length"
    assert int(u[0]) == some_numbers[3].id and \
        int(u[1]) == some_numbers[4].id and \
        int(u[2]) == some_numbers[5].id and \
        int(u[3]) == some_numbers[6].id and \
        int(u[4]) == some_numbers[7].id, "CompositeArrayNumber.from_query_IDs() populated the array with " \
                                         "incorrect results"
    # Get rid of the nodes that were created to run this test
    some_array.delete()
    [an_item.delete() for an_item in some_numbers]
