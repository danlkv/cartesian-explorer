from cartesian_explorer import Explorer
from cartesian_explorer.caches import JobLibCache
import time
import pytest

def test_quimb(tmp_path):
    quimb = pytest.importorskip('quimb')

    cache = JobLibCache(tmp_path / 'caex_cache')
    ex = Explorer(cache=cache)


    @ex.add_function(requires=('N',), provides=('rehs', 'opt_time'))
    def rehs(N):
        circ = quimb.tensor.Circuit(N)
        for i in range(N):
            circ.apply_gate('H', i)
        for i in range(N):
            circ.apply_gate('CZ', i, (i+1)%N)
        for i in range(N):
            circ.apply_gate('CX', i, (i-1)%N)

        st = time.time()
        ZZ = quimb.pauli('Z') & quimb.pauli('Z')
        infos = []
        for where in [(0,1), (1,2)]:
            rehs = circ.local_expectation_rehearse(ZZ, where)
            infos.append(rehs)
        return infos, None

    call_num = 0
    @ex.add_function(requires=('rehs',), provides=('time', 'mem'))
    def sim(rehs):
        nonlocal call_num
        call_num += 1
        print('calling sim')
        try:
            for rehs_ in rehs:
                tn = rehs_['tnh']
                info = rehs_['info']

                start = time.time()
                res = tn.contract(output_inds=(), optimize=info.path)
        except:
            print('error')
            return None, None
        return time.time()-start, res

    ti = ex.get_variable('time', N=10)
    assert call_num == 1
    mem = ex.get_variable('mem', N=10)
    assert call_num == 1
