Motivation
==========

``neoads`` was motivated by a set of needs that I found myself constantly returning to. These are probably best
presented via some illustrative examples:

1. It is not always possible to afford long connection times to a database management system (DBMS)
    * Modern "computers" (across the scale span) are fast but data processing to extract meaningful information does
      not always happen at CPU time scales. Consequently, it is not always possible to be holding a connection to
      a database open along with any potential resources this connection might be consuming. Sooner or later, the
      connection will time out or the server will run out of resources.

2. Algorithms operate over data structures, not database "resultsets".
    * `Enough said. <https://en.wikipedia.org/wiki/Algorithms_%2B_Data_Structures_%3D_Programs>`_

3. **Rapid** Prototyping.
    * When working at proof-of-concept or other projects at early stage in their development, things are in a constant
      state of change and time is scarce. In all likelihood, the problem one tries to solve is relatively "new" and
      difficult already. At this stage, any additional complexity that is inserted by the tool itself is counter
      productive. For example, `data marshalling <https://en.wikipedia.org/wiki/Marshalling_(computer_science)>`_ to
      and from a DBMS or between data processing tasks is an extremely time consuming task (especially combined with
      #2 from above).

4. "Details"
    * A certain mapper's [#f1]_ operations can be translated to queries, instead of moving large amounts of data
      back and forth between a client and a DBMS. This opens up possibilities for distributing data processing
      load between a client and a server rather than viewing the server as another serialisation target.


These experiences helped shape ``neoads`` to a Python 3 module that provides access to abstract data structures
implemented over Neo4j databases.

For more details regarding the module's design, continue to :ref:`memory-manager` or browse over the detailed
:ref:`datamodeling` section.

Finally, be sure to check the individual sections on


.. [#f1] A "mapper" in the sense of a component that acts like an `Object Relational Mapping
         <https://en.wikipedia.org/wiki/Object-relational_mapping>`_.