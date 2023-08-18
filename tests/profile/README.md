## profiling of tests with scalene

`scalene` is a python library that allows to profile CPU, memory, and GPU.


### Scalene usage

The default way to run it is via cli `scalene script.py`,
but this makes it harder to integrate with other tests.

To profile a specific function in some other (library) code:

1. add decorator `@profile` around your function. This is inconvenient, since you have to modify source code of a module.
2. The function under profile has to be in file that is a child of directory where `script.py` is located. This can be overriden via `--profile-only=<filename>` or `--profile-all`

### Scalene internals

The `scalene` command runs `scalene.scalene_profiler.Scalene.main()`
function. This function parses the arguments, and then runs
the code via [`exec`](https://github.com/plasma-umass/scalene/blob/v1.5.25/scalene/scalene_profiler.py#L1856). Essentially, it executes the code "as text".

If you run `python script.py` and call `main` in `script.py`,
the `main()` will itself read the text from `script.py` and run it.
To determine if you are "inside" the profiling, 
```python
    if globals().get('__package__')!='scalene':
        #Outside
    else:
        #Inside
```
the `globals` passed to `exec` are from `scalene.__main__`.
(this may introduce strange behavior in profiled code that relies on some assumptions on `globals`)

### Profile function in scalene

Scalene distinguishes between program file and files_to_profile.

To add `my_function` to be profiled:

1. Add its file to cli arguments, among with others

    ```python
    sys.argv = ['scalene',
                '--cpu',
                '--cli',
                '--profile-only',
                my_function.__code__.co_filename,
                *sys.argv[0:]
                ]
    ```

    This makes `Scalene.main()` think it's running in cli, while
    allowing you to run the script with `python script.py`.

2. Add it to profiled at "profile time"

    ```python
        scalene_profiler.Scalene.profile(my_function)
    ```

## Usage


```python
from profile_lib import run_profiles
from my_lib import my_func

def my_foo(N):
   return my_func(np.arange(N))

run_profiles(my_foo, args=(1000,), kwargs=dict(), (np.sum,))

```

Limitations: 

1. will not work with C functions
2. May not work with functions in multiple files
3. Memory profiling may not work


Pitfalls:

1. "program did not run for long enough to profile".

    this can mean the files for functions are not found.
    Or that there is very little time spent in those files.

2. If you don't see some of the functions in function list,
    this may mean that those functions are not taking long
    enough.
