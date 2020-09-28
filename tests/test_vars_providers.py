from cartesian_explorer import Explorer

def test_add_with_provider():
    explorer = Explorer()

    @explorer.provider
    def y(x, m):
        return x*2 + m

    calls_z = 0
    @explorer.provider(cache=False)
    def z(y):
        nonlocal calls_z
        calls_z += 1
        return calls_z + y


    zv = explorer.get_variable('z', x=1, m=5)
    assert zv == 1*2+1+5
    zs = explorer.map_variable('z', x=[1, 2, 3], m=[2])
    print(zs)
    assert all(zs == [6, 9, 12])

