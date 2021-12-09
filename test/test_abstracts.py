# """
#
# Tests significant functionality that is shared by other objects but is
# really implemented at higher levels.
# """
#
# import pytest
# import neomodel
# import neoads
#
# class StubElementVariable(neoads.ElementVariable):
#     pass
#
#
# def test_unique_variable_name():
#     u = StubElementVariable().save()
#     with pytest.raises(neomodel.UniqueProperty):
#         F = StubElementVariable(name = u.name).save()
#     u.delete()
#
# def test_named_variable():
#     u = StubElementVariable(name="SOMEVAR").save()
#     v = StubElementVariable.nodes.get(name="SOMEVAR")
#     assert type(v) is StubElementVariable
#     assert v.name == "SOMEVAR"
#     u.delete()
#
#
# def test_deletion():
#     u = StubElementVariable(name="SOMEVAR").save()
#     u.delete()
#     r, _ = neomodel.db.cypher_query("MATCH (a:ElementVariable{{name:'{nme}'}}) return a".format(nme=u.name), resolve_objects=True)
#     assert len(r)==0