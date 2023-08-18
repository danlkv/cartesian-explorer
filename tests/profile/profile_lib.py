from scalene import scalene_profiler
from logging import getLogger, basicConfig
import sys
basicConfig()
logger = getLogger('profile_lib')
logger.setLevel(5)

def run_profiles(
    func_to_run,
    profiled_funcs: tuple,
    globals,
    args=tuple(),
    kwargs=dict()
):

    logger.log(10, f'{globals=}')
    if globals.get('__package__')!='scalene':
        prof_filenames = list(set([
            func.__code__.co_filename for func in profiled_funcs
        ]))
        sys.argv = ['scalene',
                    '--cpu',
                    '--cli',
                    '--profile-only',
                    ','.join(prof_filenames),
                    *sys.argv[0:]
                    ]
        logger.log(10, f'{sys.argv=}')
        # Fix strange eror in scalene custom pywhere cpp code that adds python file
        logger.log(10, f'Running scalene')
        scalene_profiler.Scalene.main()
    else:
        scalene_profiler.Scalene.__dict__['_Scalene__args'].memory = False
        for func in profiled_funcs:
            scalene_profiler.Scalene.profile(func)
        logger.log(10, f'Starting profile')
        logger.log(10, f"{scalene_profiler.Scalene.__dict__['_Scalene__functions_to_profile']=}")
        scalene_profiler.Scalene.start()
        func_to_run(*args, **kwargs)
        scalene_profiler.Scalene.stop()
