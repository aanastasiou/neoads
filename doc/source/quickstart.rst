.. _quickstart:

Quick Start
===========

This section contains the bear minimum usage examples for a user to get up to speed with ``neoads``.

Broadly speaking, ``neoads`` supports:

* Variables of `Simple data types <https://en.wikipedia.org/wiki/Primitive_data_type>`_
    * A number (whether integer or float)
    * A date
* Variables of `Composite data types <https://en.wikipedia.org/wiki/Composite_data_type>`_
    * A String
    * Arrays of:
        * String
        * Number
        * Date
* Variables of `Abstract Data Types <https://en.wikipedia.org/wiki/Abstract_data_type>`_

Prior to making use of any of these though, ``neoads``, needs to be initialised.

Initialisation
--------------

At the moment, a typical program making use of ``neoads`` involves the following::

    import os
    import neomodel # Optionally, please see below
    import neoads

    if __name__ == "__main__":
        # Initialise neomodel
        neomodel.db.set_connection(os.environ["NEO4J_BOLT_URL"])
        # It is now possible to start using neoads from this point onwards.

This of course assumes that the ``NEO4J_BOLT_URL`` environment variable is set but more importantly shows that prior to
using ``neoads``, a valid
`neomodel connection <https://neomodel.readthedocs.io/en/latest/getting_started.html#connecting>`_ is required.

For a more detailed discussion on initialisation as well as working with ``neoads`` through ``neoads.MemoryManager``
objects, please see :ref:`this section <memory-manager>`.


Working with ``neoads`` typed variables
---------------------------------------
Just as it happens with generic programming languages, in ``neoads``, a variable has
a **name** and a **data type** that determines how computation is to be carried out with the
content of that variable.

During initialisation, **all variables** accept an optional ``name`` parameter. This name can later be
used to get a reference to a particular variable. Unnamed variables **can** exist and they are the
equivalent of a literal object. *Almost all* ``neoads`` variables can also be initialised with a
suitable (native Python) default ``value`` data type.


Working with ``Simple`` and ``Composite`` typed variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Just equipped with this basic knowledge, we can start looking at some examples of the complete
`CRUD <https://en.wikipedia.org/wiki/Create,_read,_update_and_delete>`_ lifecycle of a ``neoads`` object.

::

    # To CREATE variables, simply call their constructor with
    # the parameter's value (mandatory), name(optional) and don't
    # forget to call ``save()`` for these operations to be executed
    # at server side.


    a_number = neoads.SimpleNumber(112).save()
    a_date = neoads.SimpleDate(datetime.date(2015, 10, 21)).save()
    a_string = neoads.CompositeString("Hello World").save()


    # To name a variable...

    the_answer = neoads.SimpleNumber(42, name="answer_to_everything").save()


    # To DELETE variables, simply call `delete()`.

    a_list_of_objects = [a_number, a_date, a_string]
    [a_list_item.delete() for a_list_item in a_list_of_objects]


    # To RETRIEVE (get a reference to) a saved variable...

    some_number = neoads.SimpleNumber.nodes.get(name="answer_to_everything")


    # To UPDATE the value of that variable...

    some_number.value = 84
    some_number.save()


    # Obviously, some_number can be deleted here
    # via a call to its delete() method.

    some_number.delete()

The exact same example applies for ``SimpleDate`` with the exception that the value
argument must be a standard Python ``datetime`` object.

Working with ``CompositeArray`` typed variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Arrays are initialised in exactly the same way but also offer suitable zero based indexing through their getters and
setters

::

    # Create an unnamed Array of strings

    the_granville_brothers = neoads.CompositeArrayString(["Zantford Granville", "Thomas Granville",
                                                          "Bobby Granville", "Mark Granville",
                                                          "Edward Granville"]).save()
    print(the_granville_brothers[0])

Setting the value of an element of the array works through a corresponding "setter" **but**, for this change to
take effect **server-side**, the object's ``save()`` method has to be called. For example:

::

    the_granville_brothers[2] = "Robert Granville"
    the_granville_brothers.save()



Working with ``Abstract`` typed variables
-----------------------------------------

Abstract type values are initialised in a similar way for trivial use cases, but also have functionality that makes
them special within ``neoads``.

First of all, abstract data structures are agnostic of their content.

Therefore, there is a distinction between the data structure itself and its contents. This distinction is important
when considering the DELETE operation.

In ``neoads``, abstract data structures are **cleared** (that is, their *content* is reset) via a call to ``clear()``
but to completely *remove the variable from "memory"*, the ``destroy()`` method is called.

Contrast this to simply calling ``delete()`` when working with Simple and Composite ``neoads`` variables.

Consequently, if an attempt is made to delete an abstract data type variable without first having "cleared" it,
an exception will be thrown.

This is the only similarity between the core abstract data structures offered by ``neoads``.

``neoads`` Abstract typed variables **do not take default values** but they are meant to be initialised in rich ways
via `CYPHER <https://neo4j.com/developer/cypher-query-language/>`_ queries.

However, for completeness, each data type has suitable methods to update its contents and these will be used here to
provide some basic examples of their functionality.


Working with ``AbstractSet``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A `set <https://en.wikipedia.org/wiki/Set_(abstract_data_type)>`_ stores **unique values** in no particular order and
does not support accessors of any kind *except* for testing for set membership.

A set can also be combined with other sets via suitable operators.

An indicative CRUD session with a ``neoads.AbstractSet`` looks like this:

::

    import random


    # First, let's create a set of strings as indicative content
    # for our AbstractSet

    some_string_values = ["Alpha", "Beta", "Gamma", "Beta", "Delta"]
    some_strings = [neoads.CompositeString(k).save() for k in some_string_values]


    # Now, let's create an AbstractSet
    # Naming this set is entirely optional here.

    my_set = neoads.AbstractSet(name="MySet").save()


    # As the set is empty, its length is expected to be zero

    print(f"The length of 'MySet' is {len(my_set)}.")


    # Let's add the strings from `some_strings` here:

    my_set.add(some_strings[0])


    # This will change the length of the AbstractSet (obviously)
    print(f"The length of 'MySet' is {len(my_set)}.")


    # Let's keep adding elements, we can do this via chained calls to 'add()' too

    my_set.add(some_strings[1]).add(some_strings[2]).add(some_strings[3]).add(some_strings[4])


    # Or, we could add those strings as part of an iteration too
    [my_set.add(an_element) for an_element in some_strings[5:]]


    # At this point, the AbstractSet is initialised and its length
    # is going to be equal to the number of unique elements within 'some_string_values'
    # Let's have a look

    print(f"Unique integers in some_random_integers:{len(set(some_random_integers))}.")
    print(f"The length of MySet is {len(my_set)}.")

Once an ``AbstractSet`` is initialised, it is possible to test its contents for membership via Python's ``in`` operator.
Continuing with the above example:

::

    # Is CompositeString("Alpha") part of the AbstractSet?
    if some_strings[0] in my_set:
        print("Yes it is") # This message will be printed
    #
    # Is CompositeString("Zeta") part of the AbstractSet?
    some_other_string = neoads.CompositeString("Zeta").save()

    if some_other_string in my_set:
        print("Yes, Zeta is in the Set too") # This message will not be printed.

``AbstractSet`` can be combined via operators with other ``AbstractSet`` typed variables. For example,
the result of ``{1,2,3} - {2,3,5}`` is ``{1}``. Let's do that:

::

    # Create the two sets

    u = neoads.AbstractSet(name = "u").save()
    u.add(neoads.SimpleNumber(1).save()).add(neoads.SimpleNumber(2).save()).add(neoads.SimpleNumber(3).save())
    v = neoads.AbstractSet(name = "v").save()
    v.add(neoads.SimpleNumber(2).save()).add(neoads.SimpleNumber(3).save()).add(neoads.SimpleNumber(5).save())


    # Obtain their difference

    q = u - v


    # Check its length (at least)

    print(f"The length of q is {len(q)}")


Finally, clearing and completely deleting an ``AbstractSet`` is done via calls to:

::

    # Clear the data structure

    my_set.clear()
    print(f"The length of MySet is {len(my_set)}")

The above clears the ``AbstractSet`` but **does not remove it** from Neo4J (or, the DBMS more generally).

To do that:

::

    # Remove MySet completely

    my_set.destroy()

For much more detailed information about working with ``neoads.AbstractSet`` please see
:ref:`elsewhere in the documentation <compositedatatypes>`.


Working with ``AbstractMap``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A `Map <https://en.wikipedia.org/wiki/Associative_array)>`_ establishes a *one-to-one* relationship between a Key
and a Value.

``neoads.AbstractMap`` entities are implemented *on top of* ``AbstractSet``, in the sense that they use one
set to describe the unique keys they store and another set that creates the actual link between the Key and the
Value.

An indicative CRUD session with a ``neoads.AbstractMap`` looks like this:

::

    import random

    # First, let's create some content that will later be added to the Map

    data = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0}
    elements = [(neoads.CompositeString(an_item[0]).save(),
                 neoads.SimpleNumber(an_item[1]).save())
                for an_item in data.items()]


    # Create and populate the map

    u = neoads.AbstractMap().save()
    for a_key, a_value in elements:
        u[a_key] = a_value

The "length" (or size) of the mapping can be obtained via a simple call to ``len()``:

::

    print(f"The length of the mapping is {len(u)}")

Items in the mapping can be accessed via:

::

    print(f"The numeral representation of {elements[0][0]} is {u[elements[0][0]]}")

It is also possible to determine membership of an item within the mapping **by key** (similar to the way a `Python
dictionary <https://docs.python.org/3/tutorial/datastructures.html#dictionaries>`_ can:

::

    if elements[0][0] in u:
        print(f"The mapping contains this element") # This line will be printed.


Individual entries can be removed from the map via a simple call to Python's ``del()``:

::

    del(u[elements[0][0]])
    print(f"The length of the mapping is {len(u)}")

``AbstractMap`` is cleared and "destroyed" via the same interface as described in the ``AbstractSet`` section.

.. note::

   * It might be inferred from the above that merely trying to access an ``AbstractMap``, requires a ``neoads``
     variable that is already saved in the database.

   * It is however possible to **recall** items from an ``AbstractMap`` using an object that is not yet saved in the 
     database. This makes accesss much more straightforward.

     * For example, suppose:

       ::

           # Initialisation
           # This code creates two nodes that are attached to 
           # the set of keys and values of the AbstracMap.

           m = neoads.AbstractMap(name="m").save()
           k = neoads.CompositeString("Alpha").save()
           v = neoads.CompositeString("Something").save()
           m[k] = v
    
           # Now, given m, it is possible to do a quick lookup as:
           m[neoads.CompositeString("Alpha")]
    
           # Notice here that m simply accepts a CompositeString() that 
           # is not saved in the database.




Working with ``AbstractDLList``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A `Doubly Linked List <https://en.wikipedia.org/wiki/Doubly_linked_list>`_ is very similar to an Array (in terms of
the way it presents itself to its user) but its size is only limited by the size of the RAM.

A trivial way to instantiate an ``AbstractDLList`` is:

::

    import random


    # Create some generic content that is to be added to the DLList

    elements = [neoads.SimpleNumber(random.random()).save()
                for i in range(0, 10)]


    # Create and populate the DLList

    u = neoads.AbstractDLList().save()
    [u.append(an_element) for an_element in elements]

Calls to ``append()`` can also be chained, in a way similar to how ``neoads.AbstractMap.add()`` works.

With an instantiated list, its length can be obtained via a "natural" call to ``len()``:

::

    print(f"The length of list is {len(u)}")


The item at the :math:`n^{th}` index (here, :math:`2`) can be obtained via:

::

    some_item = u[2]

It is worth noting here that this ``AbstractDLList`` call will return an object of whatever type the :math:`n^{th}`
element of the list happens to be (here ``SimpleNumber``). Contrast this to what is returned by ``CompositeArray``
type variables.

The :math:`n^{th}` list item can also be deleted via a "natural" ``del()`` call:

::

    del(u[2])


``AbstractDLList`` can be extended by merging their contents with the contents of another ``AbstractDLList``:

::

    # Create some generic content that is to be added to the DLLists by query

    elements = [neoads.SimpleNumber(random.random()).save()
                for i in range(0, 4)]


    # Create and populate the DLLists

    u = neoads.AbstractDLList().save()
    v = neoads.AbstractDLList().save()
    v_list_name = v.name
    [u.append(an_element) for an_element in elements[0:2]]
    [v.append(an_element) for an_element in elements[2:4]]


    # Merge v into u

    u.extend_by_merging(v)

Notice here that ``extend_by_merging()`` calls can be chained too and that the items of the list are **not** iterated.

The list is extended by having the "tail" of the first, point to the "head" of the next list and then erasing the second
list. Therefore, it is possible for ``AbstractDLList`` to grow very large, very quickly, with only a few calls to the
``extend_by_merging()`` of various lists.

And finally, ``AbstractDLList`` is cleared and "destroyed" via the same interface as described previously.

What else is there?
-------------------

This quickstart guide is meant to provide a very brief exposition to the ideas behind ``neoads``.

There are a lot of details about each data structure and its performance which are outlined in other sections of
this manual.

So, please, keep reading, if you want to find out more about the ``MemoryManager``, hashing and how it is used by
``neoads``, how are operations resolving to CYPHER queries, how it is possible to construct higher level operations
in the form of queries and pass them to the backend, how are the abstract data structures preserved in the
backend (and how to query them **without** ``neoads``) and more.
