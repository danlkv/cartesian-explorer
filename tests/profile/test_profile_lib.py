from profile_lib import run_profiles
import requests

def my_foo(N):
    return requests.get(f'https://google.com/{N}')


run_profiles(my_foo, (requests.get, requests.request), globals(), args=(1000,))
