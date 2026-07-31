# Implement `CodeReclaimers/neat-python`

You are given a Python repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a `pass` statement.

You need to complete the implementations for all functions (i.e., those with `pass` statements) and pass the unit tests.
Do not change the names of existing functions or classes, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `CodeReclaimers/neat-python`
- Source directory to implement: `neat/`
- Test command: `pytest` (run against `tests`)
- Specification / docs: https://neat-python.readthedocs.io

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Next   / Welcome to NEAT-Python’s documentation!

Welcome to NEAT-Python’s documentation!

Warning Breaking Changes — cumulative through v2.1 If you are upgrading from an earlier version, note the following breaking changes: v2.0: CTRNN.create() no longer accepts a time_constant argument. Time constants are now per-node evolvable gene attributes, configured via time_constant_* parameters in the [DefaultGenome] config section. Checkpoints created with v1.x are not loadable in v2.0 or later.

v1.0: Innovation number tracking fully implemented per the NEAT paper; checkpoints from v0.x are not compatible. ThreadedEvaluator and DistributedEvaluator were removed — use ParallelEvaluator instead. All required configuration parameters must now be explicitly specified in the config file.

See the Migration Guide guide for detailed upgrade instructions.

NEAT is a method developed by Kenneth O. Stanley for evolving arbitrary neural networks.

NEAT-Python is a pure Python implementation of NEAT, with no dependencies other than the Python standard library.

Currently this library supports Python versions 3.8 through 3.14, as well as PyPy 3.

For academic researchers: See NEAT-Python for Academic Research for guidance on using neat-python in research publications.

Many thanks to the original authors of this implementation, Cesar Gomes Miguel, Carolina Feher da Silva, and Marcio Lobo Netto!

Note Some of the example code has other dependencies. For your convenience there is a conda environment YAML file in the examples directory you can use to set up an environment that will support all of the current examples. TODO: Improve README.md file information for the examples.

latest For further information regarding general concepts and theory, please see Selected Publications  on Stanley’s website, or his AMA on Reddit .

If you encounter any confusing or incorrect information in this documentation, please open an issue in the GitHub project .

Contents: Getting Started Quick Start Installation Minimal Example Run It!

What Just Happened?

Next Steps Need Help?

Installation About The Examples Install neat-python from PyPI using pip Install neat-python from source Optional extras XOR Example: Detailed Walkthrough The XOR Problem Fitness function Sample Output Common Mistakes Running NEAT Getting the results Visualizations Example Source Configuration Essentials The Big Picture Essential Parameters Annotated XOR Configuration Key Parameters Reference Parameter Relationships Common Configuration Patterns Troubleshooting Next Steps latest Understanding NEAT NEAT Overview Understanding Innovation Numbers What Are Innovation Numbers?

Why They Matter What Changed in v1.0.0 Impact on Your Code How It Works (Technical Details) References Glossary User Guides NEAT-Python for Academic Research Overview Strengths for Research Use Relationship to Canonical NEAT Key Implementation Differences Recommendations for Academic Use Configuration for Canonical Behavior Working with Deterministic Evolution Publication Guidelines Additional Considerations References Further Reading Configuration file description [NEAT] section [DefaultStagnation] section [DefaultReproduction] section [DefaultSpeciesSet] section [DefaultGenome] section Reproducibility Overview Basic Usage Parallel Mode Checkpointing Limitations Best Practices Complete Examples latest Example Scripts See Also Cookbook: Common Patterns How to: Set Specific Output Activation Functions How to: Use Parallel Evaluation How to: Use GPU-Accelerated Evaluation How to: Save and Restore Checkpoints How to: Debug “Population Not Evolving” How to: Interpret Fitness Trends How to: Control Network Complexity How to: Handle Different Output Ranges How to: Configure for Different Problem Types Common Gotchas Next Steps Customizing Behavior New activation functions New aggregation functions Reporting/logging New genome types Speciation scheme Species stagnation scheme Reproduction scheme Overview of builtin activation functions abs clamped cube exp gauss hat identity inv log relu elu lelu selu sigmoid sin softplus square tanh Continuous-time recurrent neural network implementation latest GPU-Accelerated Evaluation Network Export Quick Start Supported Network Types JSON Format Overview Complete Format Specification API Reference Converting to Other Formats Examples Design Philosophy See Also API Reference activations aggregations attributes checkpoint config ctrnn parallel genes genome graphs iznn innovation math_util nn.feed_forward nn.recurrent population reporting reproduction species stagnation statistics Genome Interface Class Methods Initialization/Reproduction Crossover/Mutation Speciation/Misc Reproduction Interface Class Methods latest Initialization Other methods Additional Resources Frequently Asked Questions Algorithm Choice Performance & Scaling Configuration Understanding Behavior Integration Academic More Questions?

Troubleshooting Guide Population Stuck at Low Fitness All Species Went Extinct Network Complexity Exploding Checkpoint Restore Errors ModuleNotFoundError for Examples Fitness Function Errors Getting More Help Migration Guide Migration from 1.x to 2.0 Migration from 0.93 to 1.0 Overview of Changes ThreadedEvaluator (Removed) DistributedEvaluator (Removed) ParallelEvaluator Improvements Additional Resources Getting Help Version Information Configuration File Migration (v1.0) What Changed What You’ll See Required Parameters by Section Complete Example Configuration Step-by-Step Migration Instructions Quick Reference: New Required Parameters Configuration Migration Resources Indices and tables Index latest Search Page latest
