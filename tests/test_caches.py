from scalene import scalene_profiler
from cartesian_explorer.caches import DirectoryCSVCache
import sys
import time
#from scalene import __main__

#sys.argv = ['scalene', *sys.argv]



def test_caches(tmpdir):
    def foo(a):
        time.sleep(0.01)
        return tuple([a, a])

    #scalene_profiler.Scalene.profile_this_code = print
    cache = DirectoryCSVCache(tmpdir)
    #cache.call = scalene_profiler.Scalene.profile(cache.call)
    #scalene_profiler.start()
    foo_c = cache(foo)
    #print(list(scalene_profiler.Scalene.__dict__['_Scalene__files_to_profile']))
    #print(scalene_profiler.Scalene.__dict__['_Scalene__functions_to_profile'])
    time.sleep(0.01)
    foo_c(foo_c(1))
    for i in range(300):
        foo_c(i)
    #scalene_profiler.stop()


#scalene_profiler.Scalene.profile(DirectoryCSVCache.call)
sys.argv = ['scalene',
            '--cpu',
            '--cli',
            '--profile-only',
            DirectoryCSVCache.call.__code__.co_filename,
            __file__,
            *sys.argv[0:]
            ]

if globals().get('__package__')!='scalene':
    print("Run scalene")
    # Fix strange eror in scalene custom pywhere cpp code that adds python file
    scalene_profiler.Scalene.__dict__['_Scalene__args'].memory = False
    scalene_profiler.Scalene.main()
else:
    print("Run th")
    scalene_profiler.Scalene.__dict__['_Scalene__args'].memory = False
    scalene_profiler.Scalene.profile(DirectoryCSVCache.call)
    scalene_profiler.Scalene.profile(DirectoryCSVCache.__init__)
    scalene_profiler.Scalene.profile(DirectoryCSVCache._lookup)
    scalene_profiler.Scalene.start()
    test_caches('/tmp/caex_tmp_test')
    scalene_profiler.Scalene.stop()
    print('thdone')

