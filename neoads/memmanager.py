"""
Establishes the memory manager object.

At the moment, the memory manager handles a very limited amount of operations but ultimately, every operation in the
future will be passing via the ``MemoryManager`` in the form of CYPHER (or augmented CYPHER) queries.

:author: Athanasios Anastasiou
:date: Mar 2019
"""

import neomodel
import os
from . import exception


# TODO: MED, The memory manager could support a list of servers to route commands to, akin to namespaces.
class MemoryManager:
    """
    A memory manager object that handles abstract data structure CRUD operations.

    .. note::

        This should be thought of like a memory context object within which, all neoads variables live. It is basically
        bounded only by the capacity of the server and network latencies.

    """
    def __init__(self, connection_uri=None, uname=None, pword=None, host="localhost", port=7687):
        """
        Initialises the manager.

        .. note::

            If none of the expected configuration parameters are provided, the constructor will try
            to initialise the object via the ``connection_uri`` environment variable. If that fails, it will
            try to initialise it via the username and password data and if that fails, then it will
            give up with an appropriate exception.

        :param connection_uri: A suitable neo4j connection URI.
        :type connection_uri: str
        :param uname: A username
        :type uname: str
        :param pword: A password
        :type pword: str
        :param host: The host the neo4j server is running on
        :type host: str
        :param port: The port number the server is running on
        :type port: int
        """
        # Setup the logger
        # logging.basicConfig(format="%(levelname)s:%(name)s:%(asctime)s:%(message)s", datefmt="%m/%d/%Y %I:%M:%S %p",
        #                     filename="insightql.log",
        #                     level=logging.INFO)
        conn_uri = None
        try:
            conn_uri = connection_uri or os.environ["NEO4J_BOLT_URL"]
        except KeyError:
            try:
                uname = uname or os.environ["NEO4J_USERNAME"]
                pword = pword or os.environ["NEO4J_PASSWORD"]
                conn_uri = "bolt://{uname}:{pword}@{host}:{port}".format(uname=uname, pword=pword, host=host, port=port)
            except KeyError:
                raise exception.MemoryManagerError("The NEO4J_USERNAME and or NEO4J_PASSWORD variables are not set."
                                             "Cannot connect to database.")
        self._connection_URI = conn_uri
        neomodel.db.set_connection(self._connection_URI)

    def list_objects(self):
        """
        Obtains a list of top level objects from the server.

        .. note::

            Similar in functionality to a dir


        :return: list[str]
        """
        object_names, _ = neomodel.db.cypher_query("MATCH (anObject:ElementVariable) return anObject.name")
        object_names = [a_name[0] for a_name in object_names]
        return object_names

    # TODO: MED, MemoryManager.get_object() can become an accessor to MemoryManager so that "memory" looks like a
    #       mapping where all variables in memory are indexed by their unique name.
    def get_object(self, an_object_name):
        """
        Returns a properly instantiated reference to a top level neoads object from the DBMS.

        :param an_object_name: The name of the object to get a reference to.
        :type an_object_name: str
        :return: ElementVariable
        """
        object_from_db, _ = neomodel.db.cypher_query("MATCH (anObject:ElementVariable{{name:'{object_name}'}}) "
                                                     "return anObject".format(
                                                    **{"object_name": an_object_name}), resolve_objects=True)
        if len(object_from_db) != 1:
            raise exception.ObjectNotFound(f"Object with name {an_object_name} not found")
        else:
            return object_from_db[0][0]

    def garbage_collect(self):
        """
        Detects "orphan" elements and deletes them.

        "Orphan" elements are:
            DLListItems that are not bound to a list
            SetElements that are not linked to a set
            Unnamed elements that are not refernced by any other data structure

        :return:
        """
        # TODO: MED, Garbage collection should become the responsibility of each type and have separate functions that
        #       the manager calls to perform garbage collection.

        # NOTE: Notice here that the order by which the garbage collection occurs is important

        # Delete orphaned maps
        neomodel.db.cypher_query("MATCH (a:AbstractMap)-[:VALUES_SET]->(:AbstractSet), (a)-[:KEYS_SET]->(:AbstractSet) WHERE a.name=~'^[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]$' AND NOT ()-[]->(a) DETACH DELETE a")

        # Delete orphan sets that are not referenced by anything. These would be unreachable.
        # This step can produce a lot of orphan intermediate abstract structure elements
        neomodel.db.cypher_query("MATCH (a:AbstractSet)-[:SET_ELEMENT]->(b:SetItem) WHERE a.name=~'^[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]$' AND NOT ()-[]->(a) DETACH DELETE a,b") 

        # Delete orphan intermediate abstract struct elements of the Double Linked List
        # Match the severed heads of lists and delete the whole path connected to them
        neomodel.db.cypher_query("MATCH (b:AbstractStructItem:DLListItem) WHERE (b)-[:DLL_NXT]->(:AbstractStructItem:DLListItem) AND (b)<-[:DLL_PRV]-(:AbstractStructItem:DLListItem) AND NOT (b)-[:DLL_PRV]->(:AbstractStructItem:DLListItem) AND NOT (b)<-[:DLL_NXT]-(:AbstractStructItem:DLListItem) WITH b MATCH p=(b)-[:DLL_NXT*]->(:AbstractStructItem:DLListItem) DETACH DELETE p;")
 
        # If anything with a generic name still lingers on after this, delete it too.
        # Delete orphan simple variables
        neomodel.db.cypher_query("MATCH (a:ElementVariable) WHERE a.name=~'^[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]$' AND NOT ()-[]->(a) DELETE a;")

    def fsck(self, recover=False, deep=False):
        """
        Returns some basic stats associated with this instance and potentiallly fixes any problems

        :param repair: Determines whether `fsck` should attempt to correct / recover any errors with the layout of the
                       entities in the DBMS.
        :type recover: bool
        :param deep: Determines whether to perform a deep recover or not. In deep recover, "orphaned" data structures
                     will be attempted to be matched to entities in the database based on their HASH value. Obviously
                     this will have to be used with care as it can be a slow operation.
        :type deep: bool
        :return: dict

        .. note::
            
            * Reports counts of:
                * "Stray" data structure items
                * "Stray" items WITH a "value" attached to them
                * "Stray" items possibly recoverable either as Lists or Sets.
                * All variables in the system
                * "Unnamed" variables
                * "RECOVERED_[]_UID" named entities

            * Tries to recover:
                * Sets (As RECOVERED_[flat_datetime]_UID)
                * Lists (Named similarly to the way Sets are named)

            * Tries to pair:
                * Stray struct items with a given hash, to items that have that hash in the database.

            * Erases:
                * Stray unrecoverable struct items.

        """
        if recover:
            # Recovers Sets (As RECOVERED_[flat_datetime]_UID)
            # Recovers Lists (Named similarly to the way Sets are named)
            # Erases stray unrecoverable struct items.
            if deep:
                # Tries to pair stray struct items with their values
                pass
            pass
        # REPORT NUMBERS AFTER THE FIX
        # Do a basic Simple Variable count
        # Count "stray" data structure items
        # Count how many of those "stray" items actually have a "value" attached to them
        # Count how many of those "stray" items are recoverable either as Lists or Sets.
        # Count all variables in the system
        # Count how many of those are "unnamed"
        # Count numbers of RECLAIMED named entities
        raise NotImplementedError("MemoryManager.fsck() not implemented yet.")

    def query(self, a_query):
        """
        Runs a (potentially augmented) CYPHER query on the DBMS and returns any results.

        :param a_query: A CYPHER or augmented CYPHER query.
        :type a_query: str
        :return: neomodel.db.cypher_query(), properly instantiated results
        """
        raise NotImplementedError("MemoryManager.query() not implemented yet.")
