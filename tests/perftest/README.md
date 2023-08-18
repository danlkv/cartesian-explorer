## Performance comparsion tests

This is a simple tool to compare the performance of different versions of code.

The goal is to compare performance over different branches 
or different algorithms.

### Design

Each test run is associated with an ordered tuple of named tags. 
The `dict(zip(tag_names, tag_values))` will give a unique identifier for a set of measurements.

`tag_names` specify a property over which to compare.

The default tags are:

- `git_branch` - when test runs, will be determined automatically
- `name` - the function name by default
- `timestamp` - unique timestamp per each run
- `commit_short_hash` - when test runs, will be determined automatically

### Usage

1. Runing benchmark:

In your test file:
```python
from measure import measure_time_once, set_measure_directory, save_measures
set_measure_directory('/tmp/measurement_foo')

def foo(x, N):
    return np.arrange(N)*x**2

for i in range(3):
    # runs with same tags will be averaged out
    measure_time_once(foo, args=(0.5, 1000), tags=dict(id=1))
measure_time_once(foo, args=(0.5, 2000), tags=dict(id=2))
save_measures()
```

The above script will generate a csv file with columns named as `tags_names`
plus column "time".

2. Running comparison:

```
$ compare.py /tmp/measurement_foo --tagname=id
```

or in code:
```python
from compare import compare_measures

compare_measures('/tmp/measurement_foo', tagname='id')
```

3. Clearing the results

```
$ compare.py /tmp/measurement_foo clear
```

or in code:
```python
from compare import clear_measures

clear_measures('/tmp/measurement_foo', tagname='id')
```

Environment variables used

- `PERFTEST_MEASURE_DIR`

## API

`measure.py`:

- `measure_time_once`
- `set_measure_directory`
- `save_metric`

`compare.py`

- `compare_measures`
