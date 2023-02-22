"""
Tests functionality that is specific to ``CompositeArrayObject`` objects.

:author: Athanasios Anastasiou
:date: March 2019
"""

from neoads import CompositeArrayObjectDict, CompositeArrayObjectList, CompositeArrayObjectDataFrame
from neoads import ElementDomain
import neomodel
import random
import pandas


class DBItem(ElementDomain):
    simple_id = neomodel.UniqueIdProperty()
    ob_tag = neomodel.StringProperty()
    pos_x = neomodel.IntegerProperty()
    pos_y = neomodel.IntegerProperty()


def test_CompositeArrayObjectDataFrame():
    items = [DBItem(ob_tag=f"DBItem_{k}", pos_x=random.randint(0,100), pos_y = random.randint(0,100)).save() for k in range(0,10)]
    query = CompositeArrayObjectDataFrame("MATCH (a:DBItem) WHERE a.ob_tag=~'DBItem_[0-9]+' RETURN a.pos_x as pos_x, a.pos_y as pos_y").save()

    ret_data = query.execute()

    assert type(ret_data) is pandas.DataFrame
    assert len(ret_data) == len(items)

    query.delete()
    for item in items:
        item.delete()
