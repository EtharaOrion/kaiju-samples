# Implement `jilljenn/tryalgo`

You are given a Python repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a `pass` statement.

You need to complete the implementations for all functions (i.e., those with `pass` statements) and pass the unit tests.
Do not change the names of existing functions or classes, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `jilljenn/tryalgo`
- Source directory to implement: `tryalgo/`
- Test command: `pytest` (run against `tests`)
- Specification / docs: 

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

pypi pypi v1.7.0 v1.7.0 python python 3 pylint pylint 10 10 coverage coverage 90% 90% Algorithms and data structures for preparing programming competitions (e.g. ICPC, see more) and coding interviews.

By Christoph Dürr and Jill-Jênn Vie.

Our book is available in French, English, Simplified and Traditional Chinese.

Documentation of tryalgo 1.4 Blog tryalgo.org in French and English Shortest paths on the graph of Paris.

To run it yourself: Algorithmic Problem Solving Install pip install tryalgo Documentation Demo: TryAlgo in Paris pip install -r examples/requirements.txt jupyter notebook # Then go to examples folder Dynamic programming some example with coin change: Des chiffres et des lettres (that inspired Countdown) Returns '((((75*3)*(100+6))-50)/25)=952' .

All algorithms are thoroughly tested. These tests can be used to practice your programming skills!

Most snippets from the book are within 76 columns (French version) or 75 columns (English version).

Usage from tryalgo import coin_change print(coin_change([3, 5, 11], 29)) # True because 29 = 6 x 3 + 0 x 5 + 1 x 11 from tryalgo.arithm_expr_target import arithm_expr_target arithm_expr_target([25, 50, 75, 100, 3, 6], 952) Tests python -m unittest Our code is checked. Using optional requirements, you can check it too: Please drop an issue.

© 2016–2023, Christoph Dürr and Jill-Jênn Vie (vie@jill-jenn.net).

Released under the MIT License.

Louis Abraham Lilian Besson Xavier Carcelle Stéphane Henriot Ryan Lahfa Olivier Marty Samuel Tardieu pip install pycodestyle pylint make pycodestyle # PEP8 make pylint Found a bug?

Authors Contributors
