# CS 131 Fall 2023: Project Starter

Hey there! This is a template repository that contains the necessary boilerplate for [CS 131](https://ucla-cs-131.github.io/fall-23-website/)'s quarter-long project: making an interpreter. The project specs are as follows:

1. [Project #1 Spec](https://docs.google.com/document/d/1RgPjCH_LtEA-e-SJhtB0hDKn6tMk5YNBcAyhAwFJehc/edit#heading=h.63zoibjlqvny)

There are three stages to the project; students are currently at the first. Thus, this folder contains the necessary bootstrapping code:

- `intbase.py`, the base class and enum definitions for the interpreter
- `brewparse.py`, which contains the `parse_program` function to parse Brewin programs
- `brewlex.py`, which contains helper functions for brewparse.py

Some notes on your submission (for Project 1)

1. You **must have a top-level, versioned `interpreterv1.py` file** that **exports the `Interpreter` class**. If not, **your code will not run on our autograder**.
2. You may also submit one or more additional `.py` modules that your interpreter uses, if you decide to break up your solution into multiple `.py` files.
3. You **should not modify/submit `intbase.py`, `brewparse.py`, or `brewlex.py`**; we will use our own when grading.

You can find out more about our autograder, including how to run it, in [its accompanying repo](https://github.com/UCLA-CS-131/fall-23-autograder).

## Licensing and Attribution

This is an unlicensed repository; even though the source code is public, it is **not** governed by an open-source license.

This code was primarily written by [Carey Nachenberg](http://careynachenberg.weebly.com/), with support from his TAs for the [Fall 2023 iteration of CS 131](https://ucla-cs-131.github.io/fall-23-website/).
