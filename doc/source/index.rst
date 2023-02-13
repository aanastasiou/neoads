.. neoads documentation master file, created by
   sphinx-quickstart on Fri Aug  3 14:04:10 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

neoads Documentation
====================

The ``neoads`` module implements ``AbstractSet``, ``AbstractMap`` and ``AbstractDLList`` (Doubly
Linked List), over a Neo4J backend.

It relies on Neomodel for the OGM functionality and is designed to minimise
round-trips to the database. In other words, if an operation can be carried out
at Server Side, ``neoads`` will execute it as a query rather than attempt to
instantiate the data structure in local memory, modify it and then push it
back to the backend.

``neoads`` data structures are implemented in a way that is:

* Agnostic to domain-specific data model
    * You can create lists, set or maps of *anything* by making ``ElementDomain`` the
      root object of your data model.

* Completely transparent to the database backend
    * The abstraction layer does not enforce a "special" organisation or
      shortcuts and it is still possible to use the values of a double linked
      list in your CYPHER queries.

Requirements
============

``neoads`` supports Python 3 (only) and ``neomodel >= 3.3.1``. It obviously requires a working installation
of ``neo4j``.

``neoads`` relies heavily on `neomodel <https://neomodel.readthedocs.io/en/latest/getting_started.html#connecting>`_
and while it is not necessary for someone to be expert in that package to use ``neoads``, some knowledge of
``neomodel`` would definitely help when going through some sections of the documentation.

Installation
============

Please install the latest release directly via ``neoads``' repository by executing a::

   pip install git+https://...

CI scripts, ``pypi`` distribution and ``readthedocs`` will shortly follow.


Contents
========
.. toctree::
   :maxdepth: 2

   quickstart
   simpledatatypes
   compositedatatypes
   abstractdatatypes
   memmanager
   motivation
   background
   datamodeling
   api



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
