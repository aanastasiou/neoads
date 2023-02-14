Writing tests for neoads
========================

If you added a feature in `neoads`, please consider adding a comprehensive test 
for its functionality.

Here is a list of handy notes we would appreciate you keeping in mind:

1. `neoads` uses [pytest](https://docs.pytest.org/en/latest/)

2. Initialisation of the database connection for all `neoads` tests
takes place in `test/conftest.py`

3. Write one test per feature you want to test

4. If your test assumes the existence of a small schema, please consider 
putting it in a separate file and importing it in your test case.

5. If more than one tests assume the existence of a small schema, please 
consider putting it in a separate file and reusing it in your different test 
cases.

6. Tests that create objects should delete them after finishing with a particular
test case.

7. Prefer to write tests that operate over **anonymous data structures**. Anonymous `neoads` data structures
receive a `uuid4` identifier as their `name` and therefore the chance that two variables end up having the 
same name is minimised. If two independent tests happen to create a Node in the backend that has the same 
name with another node then that will raise an exception that will halt the whole process.
    * For the same reason, if you are writing a test that needs to query the database for variables with 
      specific characteristics, make sure that you are querying only those specific variables and you are 
      not including anything else that might exist in the database at the same time that could also be 
      satisfying the criteria of your query. For a concrete example of this, please see the tests within
      `test_CompositeArrayNumber.py`

8. If you are writing tests for an Abstract Data Structure in `neoads`, then 
consider testing your ADS against the four fundamental operations of 
Create, Retrieve, Update, Delete (CRUD) and any other significant sub-cases 
are critical for the valid lifetime of your object.

9. If you are implementing a data type that cannot be initialised with a 
default value then test for this eventuality

10. The tests for the simple variables are:
    * Anonymous initialisation with and without a default value
    * Value validation
    * Hash value (for hashable objects)
    * Operators
    * Any other specific functionality
    * [Representative example](test_SimpleNumber.py)
    
11. The tests for the Composite variables are:
    * All tests specified for Simple Variables (where applicable)
    * Get item by key
    * Set item by key
    * Length
    * [Representative example](test_CompositeString.py)