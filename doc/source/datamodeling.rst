.. _datamodeling:

Class Diagrams & Data Modeling
==============================

The entire documentation for ``neoads`` is summarised in the following diagram:
(click on the figure to enlarge)

.. thumbnail:: resources/figures/classes.png

   The `neoads` data model.


The abstract data structures described above were originally built to support 
functionality beyond the typical operations described by the theory of abstract 
data types.

For example, the abstract data structures can hold pointers to **any** kind of 
an arbitrary data model as described by ``neomodel`` objects. They can also 
be initialised to their default values via queries that minimise the amount of 
data that are exchanged between the server and the client.

Some of this functionality will be presented here through minimal examples.

Interested readers are welcome to dive deeper into the more detailed descriptions 
of the data types and their theory that is available elsewhere in this documentation 
to deal with more complex use cases.

Abstract data structures over arbitrary data models
---------------------------------------------------

All the abstract data structures offered by the "core" ``neoads`` can point to 
arbitrary content **as long as** that content descends from a particular ``neoads`` 
entity, called ``ElementDomain``. This "content" can be as complex as it is required 
by a given domain.

In the original project that motivated its development, ``neoads`` supports a data 
model in excess of 30 entities with complex relationships between them 
(including inheritance).

The smallest demonstration here will re-use a scenario that has been done to 
exhaustion in Neo4j examples: 

A ``Person`` related to another ``Person`` living in some ``Country``.

This narrative is captured in the following data model:

::

    class PersonalRelationship(neomodel.StructredRel):
        """
        A very simple assocation class between entities of type Person that bears the date the
        acquaintance was made.
        """
        on_date = neomodel.DateTimeProperty(default_now=True)

    class Country(neoads.ElementDomain):
        uid = neomodel.UniqueIdProperty()
        name = neomodel.StringProperty()

    class Person(neoads.ElementDomain):
        uid = neomodel.UniqueIdProperty()
        full_name = neomodel.StringProperty()
        acquainted_with = neomodel.RelationshipTo("Person",
                                                  "ACQUAINTED_WITH",
                                                  model = PersonalRelationship)
        lives_in = neomodel.RelationshipTo("Country", "LIVES_IN")

The important point to notice here is that any entity that might be needed to 
be stored in some abstract data structure, **must** derive from ``ElementDomain``.

In the above example, we anticipate that for a given use case, we might need to 
create ``AbstractSet, AbstractMap`` or ``AbstractDLList`` of ``Person, Country`` 
entities.

From this point onwards, the examples assume that a Neo4J instance is available 
and that it contains data tha conform to this minimal data model.


Initialising lists via queries: The direct way
----------------------------------------------

Suppose now that we have a need to create a (doubly linked) list of ``Person`` 
entities that live within the 
`EU27 geopolitical region <https://www.gov.uk/eu-eea>`_.

With ``neoads``, this can be achieved via a simple *initialisation-by-query* call, 
as follows:

::

    # First of all create the list

    some_abstract_list = neoads.AbstractDLList(name="EU_27_PERSONS").save()


    # Then populate it

    some_abstract_list.from_query("MATCH (ListItem:Person)-[LIVES_IN]->(b:Country) "
                                  "WHERE b.name IN ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', "
                                  "'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', "
                                  "'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands', "
                                  "'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden'] ")

Notice here that ``from_query()``, accepts an **incomplete**, **READ** type CYPHER query that **must** have binded one
of its variables to the graph entity that will constitute the content of the doubly linked list.

**This binding must specifically be called ``ListItem``.**

In one phrase, what this query says is *"Run a CYPHER query and build a doubly linked list, the nodes of which point
to the query's results"*, provided here that these results are single entities of course.

In a similar way it is also possible to initialise a ``neoads.AbstractMap`` via its ``from_keyvalue_node_query()``
method.


``neoads`` data structures are interoperable
--------------------------------------------

``neoads`` abstract data structures can actually point to **any** ``PersistentElement`` 
entity, **including themselves**, because they also descend from ``PersistentElement``.

Therefore, ``neoads`` abstract data structures can contain abstract data structures that 
contain abstract data structures...ad infinitum.

This means that it is possible to piece together **any** conceivable combination such as 
an abstract list of abstract lists of abstract maps between strings and lists of sets of 
arbitrary data model entities and traverse this
`Voltron <https://en.wikipedia.org/wiki/Voltron>`_ data structure with something like:

::

    if my_entity in u[0][1][ComplexString("Something").save()][9]:
        # Do something
        pass

Notice here that ``u`` is the ``neoads`` abstract list whose ``[0]`` accessor returns a
``neoads`` abstract list, whose ``[1]`` accessor returns a ``neoads`` mapping, whose 
``[ComplexString("Something").save()]`` accessor returns a ``neoads`` abstract list, 
whose ``[9]`` accessor returns a ``neoads`` abstrac set whose ``__contains__`` operation 
is called to determine if it contains some arbitrary data model entity ``my_entity``.

For a more manageable practical example, here is a list of
lists, which can be seen as a two dimensional array:

::

    import random


    # This will be a list of 10 "rows" holding lists of 20 "columns" of SimpleNumber type elements.

    m_rows = 10
    n_cols = 20

    row_list = neoads.AbstractDLList().save()
    for a_row in range(0, m_rows):
        col_list = neoads.AbstractDLList().save()
        [col_list.append(neoads.SimpleNumber(random.random()).save())
         for k in range(0,n_cols)]
        row_list.append(col_list)

This now has initialised ``row_list`` as a doubly linked list that points to doubly 
linked lists that point to ``SimpleNumber`` type entities.

We can access any of those via:

::

    print(f"The 5,5 element is {row_list[5][5]}")


