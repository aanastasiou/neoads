Motivation
==========

**Algorithms operate over data structures, not database resultsets.**

``neoads`` attempts to treat the database as an extension to the computer's memory in the seamless 
way possible. This is achieved by abstracting the data marshalling required to convert data to and from the
backend's data format to native Python objects.

This approach offers the following benefits:

1. This "exended memory space" becomes accessible via the `Python data model <https://docs.python.org/3/reference/datamodel.html>`_,
   in which:
      
      * A ``neoads.AbstractSet`` behaves like a Set
      * A ``neoads.AbstractMap`` behaves like a ``dict``; and  
      * A ``neoads.AbstractDLList`` behaves like a List.

      * For more information please see section :ref:`abstractdatatypes`

2. ``neoads`` can work with **any existing data model** with only minor changes to the data model. This means that 
   if your data model has (for instance) an entity ``Customers``, you would be able to create a list of Customers
   sharing a particular property via ``neoads.AbstractDLList``.

      * This is taken one step further in ``neoads`` as certain operations are directly translated to queries, instead of moving 
        large amounts of data back and forth between a client and a DBMS. This opens up possibilities for distributing data processing
        load between a client and a server rather than viewing the server as another serialisation target. See also point #3 below.

      * For more information please see section :ref:`datamodeling`

3. ``neoads`` data structures can stand in as **targets** of READ Cypher queries. This means that you can quickly 
   create sub-sets of data and recall them instantly ("frozen resultsets"), rather than having to run queries every 
   time you require them [#f2]_.

4. The backend representation that supports all this functionality uses a "self-describing" schema [#f1]_, which means 
   that the data structures can be accessed / queried *without* ``neoads``. That is, the data are still readable in the 
   backend, even if they have to be accessed by raw queries.


-----

.. [#f1] ``neoads`` does establish a very simple self-describing schema for its data structures that conceptually maps 
         the data organisation and is very easy to re-use in custom queries.

.. [#f2] This benefit applies mostly to subsets that are seldomly updated. Just as it works with any "frozen" list of 
         items, if the values of the items change, the list would have to be refreshed to depict their new state.

