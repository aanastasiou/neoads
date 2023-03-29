.. _background:

The ``neoads`` Memory Space
===========================

The objective of this section is to provide a broad overview of some general ideas behind the design of ``neoads`` that
will become useful when considering its operation in more detail in later sections.

The main point that this section is making is that ``neoads`` turns the Neo4J backend to one large memory space
similar to the computer's Random Access Memory (RAM).


A computer's RAM
----------------
A computer's [#f1]_ RAM supports two operations over WORDs, those of READ and WRITE, each requiring an ADDRESS.

These operations take place in WORD boundaries with varying word lengths depending on hardware architecture
and / or the operations themselves.

RAM is accessed via an ADDRESS that is an integer number, and it can well be the result of a mathematical operation.
That is, it is possible to access memory indirectly via the use of
`pointers <https://en.wikipedia.org/wiki/Pointer_(computer_programming)>`_.

Given an ADDRESS, computers WRITE and READ data to/from RAM without really knowing how to interpret those data (e.g.
a record that holds information about a Person, is still a contiguous block of memory as far as a duplication operation
is concerned). The only type of word that computers really work with is the Integer [#f2]_.

The majority of these operations are invisible to users of higher level programming languages. Those languages abstract
RAM transactions (and other data validity checks) retaining only the basic nature of memory access.

In a language like Python, for example, WORDs in memory are accessed via variables that instead of ADDRESS have human
readable names and instead of operations like *"Write [0x0B, Ox0E, x0E] beginning at 0xF16"*, use "assignment"
(``my_variable = 4096``). Higher level languages also add two more operations to READ, WRITE in order to RESERVE and
RELEASE a range of memory ADDRESSes that are allocated for a specific purpose (e.g. C's ``malloc(), free()``).

The two most important characteristics of a "variable" in a higher level programming language are its:

1. **Name**; and
2. **Data Type**

When a variable is initialised within the `scope <https://en.wikipedia.org/wiki/Scope_(computer_science)>`_ of a
a process or function, an entry is made on a look up table that **associates** its *logical name* (``my_scream``,
``your_scream``, ``the_icecream``, etc) with its *physical* name (or in other words its ADDRESS in *some* part of
memory).

The logical name of the variable enables a programmer to refer to the variable and its data type determines how to treat
the variable.

At its most elementary form, a data type is a set of valid values associated with that data type. More advanced forms of
data types also include the permitted operations over those data types making the definition even more specific.

The most basic example of a data type is :math:`Boolean = \left\{ \varnothing, 0, 1, True, False \right\}` .

A variable declared as :math:`Boolean` is expected to take **valid** values :math:`0,1, True, False` plus the case when
it is *uninitialised* or *missing* (but even though it might be uninitialised it still retains its :math:`Boolean`
character).

And, although the trigonometric function :math:`\cos()` can be called with a :math:`Boolean` argument, its return value
would be indeterminate since :math:`\cos()` does not "make sense" over the :math:`Boolean` data type.



The Neo4J "RAM"
---------------

Database Management Systems (DBMS) [#f3]_ abstract the memory operations of RESERVE, WRITE, READ, RELEASE over Silicon
(mostly) RAM to the four operations of `CREATE, RETRIEVE, UPDATE, RELEASE (CRUD)
<https://en.wikipedia.org/wiki/Create,_read,_update_and_delete>`_ over abstract (and to an extent, completely
arbitrarily shaped) **storage** and by doing so it is possible to express these
operations through a `query language <https://en.wikipedia.org/wiki/Query_language>`_.

A full exposition of DBMS data models, their differences, how they affect their query languages and other awesomely
ultra cool details are...outside of the scope of this section, but the interested reader can find more information
in the relevant bibliography.

The backend of choice for ``neoads`` is Neo4J's Graph Database which, as all graph databases do, has one important
feature:

It can **point** through the use of directed relationships.

In a `Graph <https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)>`_ Database, data are organised in Nodes
that are connected by Relationships. More importantly, **every** Node preserves a record of its Relationships with
other Nodes. This tight integration and distribution of Relationships across the Graph is what enables fast queries over
patterns of connectivity.

Treating Nodes as "objects of some data type" and Relationships as "pointers to other objects", it is possible to treat
**storage** as a `heap <https://en.wikipedia.org/wiki/Memory_management#HEAP>`_ of memory.

Consequently, allocating memory on a heap of RAM becomes equivalent to CREATing an "object of some type" in **storage**
that can be referenced by some **name**.

This high level description includes two further points:

1. Obviously, one of the questions here is: *What should these "objects of some type" be?*; but also
2. Having decided on the "objects", the DBMS is already using its own data types by which it is possible to model a
   specific domain. Therefore, there is a further data modeling task there to **adapt** the structure and functionality
   of those objects to the way the DBMS works.

In other words, ideally, the way these "objects" are stored in the DBMS should still "make sense", leaving the data
fully queryable rather than in a state that makes sense *only* to the component that performs the mapping.



The ``neoads`` implementation
-----------------------------

``neoads`` uses ``neomodel`` as the Object Graph Mapping component to offer a first implementation of
fundamental abstract data structures (and a few assisting entities) over a Neo4J DBMS.

More importantly, it is possible to express all operations of these data structures **natively** through Neo4J's
CYPHER query language and its data types, which means that the data remain usable (that is, perfectly interpretable
and queryable) even in the absence of the mapping software.

Since it is possible to express these operations via queries, ``neoads`` is "packaging" this functionality in a
Python Application Programming Interface (API) that exposes these data structures to Python software **as naturally as
possible**.

This means that if an algorithm is supposed to operate over *"A list of objects"* then this is exactly what is
expressed via Python code. The only difference being that this *"list"*, looks like a ``list`` (``a=list()``),
behaves like a ``list`` (``a[2]="Some Content"``), but instead of "living" in RAM, it is implemented in **storage**.

The design of ``neoads`` is completely agnostic to the type of "objects" it is supposed to host. This means, that its
functionality can be used by other software so long as that software's data model conforms to a minimal set of
``neoads`` specifications.

Because of this feature, abstract data structures in ``neoads`` can be composed in **any** way conceivable, in exactly
the same way as it is possible in Python to structure something like ``U = [1,2,[[4,6],{1:"One", 2:"Two", 3:"Three", 4:{
"Apple", "Orange", "Pear"}}]`` and test for membership like ``"Apple" in U[2][1][4]``.


The functionality of this module is probably best demonstrated via an example, so for a quick overview of its
capabilities, head over to :ref:`quickstart`.

However, much more information on each object separately is available in sections :ref:`simpledatatypes`,
:ref:`compositedatatypes`, :ref:`abstractdatatypes`.







.. [#f1] "Computer" is used here in the more general sense of a computing unit. Not strictly implying a desktop
          computer. Specifically, anything that runs Python (and ``neoads``) would fit this description.
.. [#f2] Modern computers can also understand Real numbers of varying precision but they certainly cannot work with
         something like a complex data type.
.. [#f3] Database used to be spelled as "Data Base"...Mind blown.
