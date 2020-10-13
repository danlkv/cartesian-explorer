from cartesian_explorer import Explorer
import pytest

def test_resolve_linear():
    explorer = Explorer()

    @explorer.add_function(provides=('y'), requires=('x',))
    def y(x):
        pass

    @explorer.add_function(provides=('z',), requires=('y',))
    def z(y):
        pass

    @explorer.add_function(provides=('k',), requires=('z',))
    def k(z):
        pass

    funcs_to_call = explorer._resolve_call(need=('k',), have=('x',))
    print('linear when have x', funcs_to_call)
    assert len(funcs_to_call) == 3

    funcs_to_call = explorer._resolve_call(need=('k',), have=('y',))
    print('linear when have y', funcs_to_call)
    assert len(funcs_to_call) == 2

def test_resolve_complex():
    explorer = Explorer()

    @explorer.add_function(provides=('x'), requires=('a',))
    def x(a): pass

    @explorer.add_function(provides=('y'), requires=('x','m','n'))
    def y(x): pass

    @explorer.add_function(provides=('m','n'), requires=('y',))
    def mn(y): pass


    with pytest.raises(RuntimeError) as e:
        funcs_to_call, all_requires = explorer._resolve_call(need=('y',), have=('a',))
    assert 'circular' in str(e.value)
    assert 'provider' in str(e.value)

    funcs_to_call = explorer._resolve_call(need=('y',), have=('a', 'm', 'n'))
    print('comlex with amn', funcs_to_call)
    assert funcs_to_call == (y, x)

    funcs_to_call = explorer._resolve_call(need=('y',), have=('x', 'm', 'n'))
    print('comlex with xmn', funcs_to_call)
    assert (funcs_to_call) == (y, )

class Person:
    def __init__(self, name, surname, age):
        self.name = name
        self.surname = surname
        self.age = age

def test_resolve_call():
    explorer = Explorer()

    # Simple call

    @explorer.add_function(provides='version')
    def version():
        return 12

    ver = explorer.get_variable('version')
    assert ver == 12

    # Complex call

    @explorer.add_function(provides=('surname','middlename'), requires='name')
    def surname(name):
        return {'John': ('Doe', None), 'Martin':('King', 'Luther')}[name]

    @explorer.add_function(provides='age', requires=('name',))
    def age(name):
        return {'John': 12, 'Martin': 15}[name]

    @explorer.add_function(provides=('person', ), requires=('name','age','surname'))
    def make_person(name, surname, age):
        return Person(name, surname, age)



    person = explorer.get_variable('person', name='John')
    print(person)
    assert person.age == 12
    assert person.surname == 'Doe'

    person = explorer.get_variable('person', name='Martin')
    print(person)
    assert person.age == 15

    middle = explorer.get_variable('middlename', name='Martin')
    assert middle == 'Luther'

    people = explorer.map_variable('person', name=['Martin', 'John'])
    assert len(people) == 2
    assert people[0].name == 'Martin'
    assert people[0].age == 15

def test_provider_and_opts():
    explorer = Explorer()

    # Simple call

    @explorer.provider
    def sq(sum):
        return sum*sum

    @explorer.provider
    def sum(x, y=12):
        return x+y

    z = explorer.get_variable('sq', x=10)
    assert z == (10+12)**2
    z = explorer.get_variable('sq', x=10, y=8)
    assert z == (10+8)**2


