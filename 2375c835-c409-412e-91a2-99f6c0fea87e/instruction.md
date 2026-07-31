# Implement `jasondelaat/pymonad`

You are given a Python repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a `pass` statement.

You need to complete the implementations for all functions (i.e., those with `pass` statements) and pass the unit tests.
Do not change the names of existing functions or classes, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `jasondelaat/pymonad`
- Source directory to implement: `pymonad/`
- Test command: `pytest` (run against `tests`)
- Specification / docs: https://jasondelaat.github.io/pymonad_docs/

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Pymonad Documentation Project Table of Contents Tutorials How-to Guides Explanations Reference Tutorials How-to Guides How to install pymonad with pipenv Writing and using curried functions Function composition Explanations What's a monad?

Reference The Pymonad reference documentation can be found here.

Author: Jason DeLaat Created: 2021-02-01 Mon 05:55 Validate How to install pymonad with pipenv pipenv combines the functionality of pip and virtualenv on a per project basis. It's pretty easy to use and it sets up your virtual environments automatically.

If you haven't already installed pipenv we'll do that first.

Once pipenv is installed there are two ways that you can install pymonad for local development.

1. Install from the Python Package Index (PyPI) 2. Install from the source distribution Installing from PyPI Start by creating a folder for your project and navigating into it.

Then use pipenv to install pymonad .

This command will automatically create a virtual environment in the MyProject directory and adds two files, Pipfile and Pipfile.lock . The --three flag ensures that pipenv creates a virtual environment for python3 which is required for pymonad .

Installing from source To install pymonad from source, first download the source code from bitbucket. You can either download the project as a zip archive here, or clone the repository with git .

Put the pymonad directory somewhere that makes sense and then create and navigate to your project directory.

And use pipenv to install. Assuming you've put the pymonad directory in ~/lib/ then you would type: pip install pipenv bash mkdir MyProject cd MyProject bash pipenv --three install pymonad bash git clone https://bitbucket.org/jason_delaat/pymonad.git bash mkdir MyProject cd MyProject bash Checking that it works If everything worked correctly you can activate your virtual environment with: Now, launch the python REPL And import the pymonad.tools module.

If you don't get an error message then everything is working correctly.

Author: Jason DeLaat Created: 2021-02-01 Mon 05:55 Validate pipenv --three install -e ~/lib/pymonad bash pipenv shell bash python bash import pymonad.tools Python How to write and use curried functions Creating curried functions is pretty straight-forward with pymonad. The tools module provides the function curry which allows you to turn any function, including python built-ins and functions which take variable numbers of arguments, into curried functions.

curry takes two parameters: The first parameter is the number of arguments to curry and the second argument is the actual function. For instance given the following function: We create a curried version like this: If a function takes a variable number of arguments you can create multiple curried versions easily.

Whether this is a good idea or not is left as an exercise for the reader.

curry is itself a curried function so you can partially apply it and use it as a decorator to define curried functions easily: Author: Jason DeLaat Created: 2021-02-01 Mon 05:55 from pymonad.tools import curry Python def add(x, y): return x + y Python curried_add = curry(2, add) # Or, if you don't need the original #add = curry(2, add) Python curried_map = curry(2, map) # Takes a function and a single list curried_map2 = curry(3, map) # Takes a function and two lists # etc...

Python @curry(2) def add(x, y): return x + y three = add(1, 2) add_1 = add(1) also_three = add_1(2) Python Validate Function Composition Function Composition There are two ways to handle basic function composition with pymonad: Compose and Pipe . Both are really just aliases for the Reader monad with names that are a bit more semantically meaningful for the way that they're used, while Reader itself is used slightly differently.

Compose Compose takes a series of functions and combines them in a feed-forward manner producing a new function.

Pipe Pipe is similar to Compose but rather than starting with a function it starts by taking in a value and then feeding it through the following functions.

from pymonad.reader import Compose def add_1(x): return x + 1 def mul_3(x): return 3 * x # Creates a new function that first adds 1, then multiplies by 3, and # finally converts the result to a string.

new_func = (Compose(add_1) .then(mul_3) .then(str) ) print(new_func(2)) # '9' Python from pymonad.reader import Pipe def add_1(x): return x + 1 def mul_3(x): return 3 * x result = (Pipe(2) .then(add_1) .then(mul_3) .then(str) .flush() ) Python There are two things to note here.

1. While Compose results in a new function, Pipe produces a result.

2. In order to access the result you need to call flush() at the end of the pipe operation.

Pipe is the only construct in pymonad with a defined operator: The unary +. The unary + operator typically just returns the value it's given without modifying it in any way. With Pipe it's used to return the value which the pipe produces. In other words, you can use '+' instead of flush() , like so: Footnotes: Since Pipe is based on the Reader monad, without flush() you would actually get a function as a result. That function, however, would ignore it's input and always give the same result. flush() simply calls this function with dummy input and gives you back the result.

Author: Jason DeLaat Created: 2021-02-01 Mon 05:55 Validate print(result) # '9' 1 result = (+Pipe(2) .then(add_1) .then(mul_3) .then(str) ) print(result) # '9' Python 1 What's a monad?

Note: The following explanation is based on this post by Bartosz Milewski.

Introduction Monads are famously misunderstood. They've been likened to space suits, toxic waste and who knows what else.

Depending on who you ask you might be told that monads are about: Order of evaluation Since languages that provide monads by default tend to be pure functional and declarative, we don't usually know the exact order of evaluation. Whatever else they may do, the main thing we use monads for, the story goes, is to enforce a particular order of evaluation in places where that is important.

Side effects and IO Pure functional languages ban side effects so handling things like mutable state, errors and IO don't work the way most of us are used to. Monads allow us to do side effect-like things in a pure functional context.

Monads are used for these things but that's not really what they are or what they're about and focusing too much on those aspects tends to confuse the situation. What monads actually are is deceptively simple: monads are function composition.

A simple logging example At least as far as programmers need to worry about them, monads are basically just a type of function composition. If you understand how function composition works, you pretty much understand monads.

So let's see how this works. For the purposes of explanation we need a way to compose functions. Pymonad has a Compose construct for this purpose but it's built on top of the Reader monad and I don't want to use a monad to explain monads. So we'll use this instead: Many languages that have a composition operator compose functions right-to-left but for a named composition function I prefer the semantics of composing left-to-right, so the above function evaluates f first and then feeds the result to g .

Alright, so suppose we're writing some program and we have these two functions: And somewhere in our program we commpose those two functions like so: def compose(f, g): return lambda x: g(f(x)) Python def add_7(x): return x + 7 def mul_5(x): return x * 5 Python composed_arithmetic = compose(add_7, mul_5) # ... more code ...

Python So far so good. The problem comes when we decide it would be great if our functions created a log. We don't want to mutate global state and it's not really the job of our functions to know anything about the entire log so we just have our functions return a string along with the result that we were returning before.

But as soon as we do that, we've broken composed_arithmetic . add_7 is returning a tuple but mul_5 is expecting just a number. Importantly: We still want to be able to compose these functions like we did before; the overall behaviour of the system should be the same just with added logging; we need to do it in a way that deals with the logging information. So what do we do? We change how composition works!

And then we update the composition: Now you can add logging to any functions you want and if you were composing those functions all you need to do is switch to using compose_with_logging and everything will work as expected.

If we must use metaphores when talking about monads then we should at least use one that's relevant to programming. The functions above return a value that we're actually interested in and some additional metadata. In this case the metadata is logging information, in other cases it might be error states, mutable state, or something else. But in all cases adding metadata to the return types of our functions breaks composition forcing us to redefine composition in a way that takes the metadata into account.

That's a monad.

All monad types are tuples in disguise The above example is a simplified version of the Writer monad. In a sense, the monad's type is the tuple returned from each of the functions: (int, string).

some_var = composed_arithmetic(6) # result: 65 def add_7(x): return x + 7, 'Adding 7 to input {}\n'.format(x) def mul_5(x): return x * 5, 'Multiplying input {} by 5\n'.format(x) Python def compose_with_logging(f, g): def _compose_internal(x): fx, f_log = f(x) gx, g_log = g(fx) return gx, f_log + g_log return _compose_internal Python composed_arithmetic = compose_with_logging(add_7, mul_5) # ... more code ...

# This doesn't change!
