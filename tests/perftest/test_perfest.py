from measure import measure_time_once, set_measure_directory, save_measures
from compare import compare_measures, clear_measures


DIR = '/tmp/perftest_test'

def foo(n, x):
    return sum((x+i)**2 for i in range(n*2))

set_measure_directory(DIR)
measure_time_once(foo, args=(100, 10), tags=dict(id=1))
measure_time_once(foo, args=(100, 10), tags=dict(id=1))
measure_time_once(foo, args=(200, 10), tags=dict(id=2))
measure_time_once(foo, args=(200, 10), tags=dict(id=2))
save_measures()

#compare_measures(DIR, tagname='git_branch')
compare_measures(DIR, tagname='timestamp')
#clear_measures(DIR)
