from __future__ import annotations
import inspect
from typing import Any
from dataclasses import dataclass

def _maybe_unwrap(func):
    if hasattr(func, '__wrapped__'):
        return func.__wrapped__
    else:
        return func

def _defaults_len(spec):
    try:
        return len(spec.defaults)
    except (AttributeError, TypeError):
        return 0

@dataclass
class FunctionDefInfo:
    """
    Class to store function definition information.

    The intent of this class is 
    1. To provide easy access to required and optional arguments

    2. To detect changes in a function that would change
       in behavior. Just checking the source code may not be enough, 
       since the code may depend on values in the closure.
       (advanced)

    Currently, the closure values are not checked, but are
    just recorded by name.

    Properties:
        args: tuple of names of required arguments (without defaults)
        kwargs: map of arguments and their defaults
        accepts_varkw: if function accepts variadic keyword arguments
        source: source code if available
        code_freevars: names of variables referenced in the closure
        file: file of the definition if available
        spec: inspect.FullArgSpec
    """

    args: tuple[str]
    kwargs: dict[str, Any]
    accepts_varkw: bool
    source: str | None
    code_freevars: tuple[str] | None
    file: str | None
    spec: inspect.FullArgSpec | None

    @classmethod
    def from_function(cls, fn, advanced=True):
        # defaults
        args = tuple()
        kwargs = {}
        accepts_varkw = False
        source = None
        code_freevars = None
        file: str | None = None
        try:
            spec = inspect.getfullargspec(fn)
        except TypeError:
            return cls(args, kwargs, accepts_varkw, source, code_freevars, file, None)
        _required_len = len(spec.args) - _defaults_len(spec)
        args = tuple(spec.args[:_required_len])
        # -- Keyword arguments (with defaults)
        if spec.defaults:
            kwargs = dict(zip(
                spec.args[_required_len:],
                spec.defaults
            ))
            if spec.kwonlydefaults:
                kwargs.update(spec.kwonlydefaults)
        # -- Accepts arbitrary keyword arguments?
        if spec.varkw:
            accepts_varkw = True
        if advanced is False:
            return cls(args, kwargs, accepts_varkw, source, code_freevars, file, None)
        # --- Source code
        try:
            source = inspect.getsource(fn)
        except TypeError:
            pass
        # --- Variables referenced in closure
        if hasattr(fn, '__code__'):
            code_freevars = fn.__code__.co_freevars
        # --- Try to guess file of the function
        _module = inspect.getmodule(fn)
        if _module:
            if hasattr(_module, '__file__'):
                file = _module.__file__
        return cls(args,
                   kwargs,
                   accepts_varkw,
                   source,
                   code_freevars,
                   file,
                   spec)

def get_required_argnames(func):
    info = FunctionDefInfo.from_function(_maybe_unwrap(func), advanced=False)
    return tuple(info.args)

def get_optional_argnames(func):
    info = FunctionDefInfo.from_function(_maybe_unwrap(func), advanced=False)
    return tuple(info.kwargs.keys())
