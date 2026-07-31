# Implement `btclib-org/btclib`

You are given a Python repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a `pass` statement.

You need to complete the implementations for all functions (i.e., those with `pass` statements) and pass the unit tests.
Do not change the names of existing functions or classes, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `btclib-org/btclib`
- Source directory to implement: `btclib/`
- Test command: `pytest` (run against `tests`)
- Specification / docs: 

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

typing — Support for type hints Added in version 3.5.

Source code: Lib/typing.py Note: The Python runtime does not enforce function and variable type annotations. They can be used by third party tools such as type checkers, IDEs, linters, etc.

This module provides runtime support for type hints.

Consider the function below: The function surface_area_of_cube takes an argument expected to be an instance of float, as indicated by the type hint edge_length: float. The function is expected to return an instance of str, as indicated by the -> str hint.

While type hints can be simple classes like float or str, they can also be more complex. The typing module provides a vocabulary of more advanced type hints.

New features are frequently added to the typing module. The typing_extensions package provides backports of these new features to older versions of Python.

See also: Typing cheat sheet A quick overview of type hints (hosted at the mypy docs) Type System Reference section of the mypy docs The Python typing system is standardised via PEPs, so this reference should broadly apply to most Python type checkers. (Some parts may still be specific to mypy.)

Static Typing with Python Type-checker-agnostic documentation written by the community detailing type system features, useful typing related tools and typing best practices.

Specification for the Python Type System The canonical, up-to-date specification of the Python type system can be found at Specification for the Python type system.

Type aliases A type alias is defined using the type statement, which creates an instance of TypeAliasType. In this example, Vector and list[float] will be treated equivalently by static type checkers: def surface_area_of_cube(edge_length: float) -> str: return f"The surface area of the cube is {6 * edge_length ** 2}."

type Vector = list[float] def scale(scalar: float, vector: Vector) -> Vector: return [scalar * num for num in vector] Type aliases are useful for simplifying complex type signatures. For example: The type statement is new in Python 3.12. For backwards compatibility, type aliases can also be created through simple assignment: Or marked with TypeAlias to make it explicit that this is a type alias, not a normal variable assignment: NewType Use the NewType helper to create distinct types: The static type checker will treat the new type as if it were a subclass of the original type. This is useful in helping catch logical errors: You may still perform all int operations on a variable of type UserId, but the result will always be of type int. This lets you pass in a UserId wherever an int might be expected, but will prevent you from accidentally creating a UserId in an invalid way: # passes type checking; a list of floats qualifies as a Vector.

new_vector = scale(2.0, [1.0, -4.2, 5.4]) from collections.abc import Sequence type ConnectionOptions = dict[str, str] type Address = tuple[str, int] type Server = tuple[Address, ConnectionOptions] def broadcast_message(message: str, servers: Sequence[Server]) -> None: ...

# The static type checker will treat the previous type signature as # being exactly equivalent to this one.

def broadcast_message( message: str, servers: Sequence[tuple[tuple[str, int], dict[str, str]]] ) -> None: ...

Vector = list[float] from typing import TypeAlias Vector: TypeAlias = list[float] from typing import NewType UserId = NewType('UserId', int) some_id = UserId(524313) def get_user_name(user_id: UserId) -> str: ...

# passes type checking user_a = get_user_name(UserId(42351)) # fails type checking; an int is not a UserId user_b = get_user_name(-1) # 'output' is of type 'int', not 'UserId' output = UserId(23413) + UserId(54341) Note that these checks are enforced only by the static type checker. At runtime, the statement Derived = NewType('Derived', Base) will make Derived a callable that immediately returns whatever parameter you pass it.

That means the expression Derived(some_value) does not create a new class or introduce much overhead beyond that of a regular function call.

More precisely, the expression some_value is Derived(some_value) is always true at runtime.

It is invalid to create a subtype of Derived: However, it is possible to create a NewType based on a ‘derived’ NewType: and typechecking for ProUserId will work as expected.

See PEP 484 for more details.

Note: Recall that the use of a type alias declares two types to be equivalent to one another. Doing type Alias = Original will make the static type checker treat Alias as being exactly equivalent to Original in all cases. This is useful when you want to simplify complex type signatures.

In contrast, NewType declares one type to be a subtype of another. Doing Derived = NewType('Derived', Original) will make the static type checker treat Derived as a subclass of Original, which means a value of type Original cannot be used in places where a value of type Derived is expected. This is useful when you want to prevent logic errors with minimal runtime cost.

Added in version 3.5.2.

Changed in version 3.10: NewType is now a class rather than a function. As a result, there is some additional runtime cost when calling NewType over a regular function.

Changed in version 3.11: The performance of calling NewType has been restored to its level in Python 3.9.

Annotating callable objects Functions – or other callable objects – can be annotated using collections.abc.Callable or deprecated typing.Callable. Callable[[int], str] signifies a function that takes a single parameter of type int and returns a str.

For example: from typing import NewType UserId = NewType('UserId', int) # Fails at runtime and does not pass type checking class AdminUserId(UserId): pass from typing import NewType UserId = NewType('UserId', int) ProUserId = NewType('ProUserId', UserId) from collections.abc import Callable, Awaitable def feeder(get_next_item: Callable[[], str]) -> None: ... # Body def async_query(on_success: Callable[[int], None], The subscription syntax must always be used with exactly two values: the argument list and the return type. The argument list must be a list of types, a ParamSpec, Concatenate, or an ellipsis (...). The return type must be a single type.

If a literal ellipsis ... is given as the argument list, it indicates that a callable with any arbitrary parameter list would be acceptable: Callable cannot express complex signatures such as functions that take a variadic number of arguments, overloaded functions, or functions that have keyword-only parameters. However, these signatures can be expressed by defining a Protocol class with a __call__() method: Callables which take other callables as arguments may indicate that their parameter types are dependent on each other using ParamSpec. Additionally, if that callable adds or removes arguments from other callables, the Concatenate operator may be used. They take the form Callable[ParamSpecVariable, ReturnType] and Callable[Concatenate[Arg1Type, Arg2Type, ..., ParamSpecVariable], ReturnType] respectively.

Changed in version 3.10: Callable now supports ParamSpec and Concatenate. See PEP 612 for more details.

See also: The documentation for ParamSpec and Concatenate provides examples of usage in Callable.

Generics Since type information about objects kept in containers cannot be statically inferred in a generic way, many container classes in the standard library support subscription to denote the expected types of container elements.

on_error: Callable[[int, Exception], None]) -> None: ... # Body async def on_update(value: str) -> None: ... # Body callback: Callable[[str], Awaitable[None]] = on_update def concat(x: str, y: str) -> str: return x + y x: Callable[..., str] x = str # OK x = concat # Also OK from collections.abc import Iterable from typing import Protocol class Combiner(Protocol): def __call__(self, *vals: bytes, maxlen: int | None = None) -> list[bytes]: ...

def batch_proc(data: Iterable[bytes], cb_results: Combiner) -> bytes: for item in data: ...

def good_cb(*vals: bytes, maxlen: int | None = None) -> list[bytes]: ...

def bad_cb(*vals: bytes, maxitems: int | None) -> list[bytes]: ...

batch_proc([], good_cb) # OK batch_proc([], bad_cb) # Error! Argument 2 has incompatible type because of # different name and kind in the callback from collections.abc import Mapping, Sequence class Employee: ...

Generic functions and classes can be parameterized by using type parameter syntax: Or by using the TypeVar factory directly: Changed in version 3.12: Syntactic support for generics is new in Python 3.12.

Annotating tuples For most containers in Python, the typing system assumes that all elements in the container will be of the same type. For example: list only accepts one type argument, so a type checker would emit an error on the y assignment above. Similarly, Mapping only accepts two type arguments: the first indicates the type of the keys, and the second indicates the type of the values.

Unlike most other Python containers, however, it is common in idiomatic Python code for tuples to have elements which are not all of the same type. For this reason, tuples are special-cased in Python’s typing system. tuple accepts any number of type arguments: # Sequence[Employee] indicates that all elements in the sequence # must be instances of "Employee".

# Mapping[str, str] indicates that all keys and all values in the mapping # must be strings.

def notify_by_email(employees: Sequence[Employee], overrides: Mapping[str, str]) -> None: ...

from collections.abc import Sequence def first[T](l: Sequence[T]) -> T: # Function is generic over the TypeVar "T" return l[0] from collections.abc import Sequence from typing import TypeVar U = TypeVar('U') # Declare type variable "U" def second(l: Sequence[U]) -> U: # Function is generic over the TypeVar "U" return l[1] from collections.
