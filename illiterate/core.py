"""This module contains the classes that represent the types of content 
inside a Python file and perform the necessary conversions.
"""

# To represent the different types of content in a single Python file, 
# we will use two classes.
# These classes will represent, respectively, a block of Python code
# and a block of Markdown code.

# The only difference between these two types of content that we care of
# is how they are printed as Markdown.
# Other than that, both types of content are simply a list of text lines.

# There is however one common functionality for both.
# Depending on how the file is structured, we might end up with
# spurious empty lines at the begining or end of any block.
# This might not be a big issue for Markdown, in some cases, but it is
# definitely a problem for Python code.
# Hence, we will remove all the empty lines at the begining and the end
# of each block.

# The common functionality will go into an abstract class.

import abc
from typing import Iterable, TextIO, List

# ## Content Blocks

# The only relevant functionality in this class is cleaning up
# the list of content.
# We also define abstract method `print` which inheritors
# will override to determine how different types of content are printed.

class Block(abc.ABC):
    def __init__(self, content: List[str]):
        while content:
            if not content[0].strip(): # testing for emptyness
                content.pop(0)         # from the top down
            else:
                break

        while content:
            if not content[-1].strip(): # testing for emptyness
                content.pop()           # from the bottom up
            else:
                break

        self.content = content

    @abc.abstractmethod
    def print(self, fp: TextIO):
        pass


# Markdown blocks are either formed by lines starting with `#`
# (i.e., Python comments) or blank lines.
# For every line that starts with `#_`, we simply remove the first two
# characters, i.e., the sharp symbol and the starting space.
# For blank lines, we just output them as-is. 

class Markdown(Block):
    def print(self, fp: TextIO):
        for line in self.content:
            if line.startswith("# "):
                fp.write(line[2:])
            else:
                fp.write("\n")

        fp.write("\n")

# Python blocks are even easier, since we will print them as-is.
# The only point to keep in mind is to output a Markdown fenced code block
# before and after the actual code.

class Python(Block):
    def print(self, fp: TextIO):
        if not self.content:
            return

        fp.write("```python\n")

        for line in self.content:
            fp.write(line)

        fp.write("```\n\n")

# Once we have our content types correctly implemented, we will
# define a container class that stores a sequence of possible `Block`s.
# This will make it easier later to dump a bunch of different blocks with
# a single instruction.

class Content:
    def __init__(self, *content: Iterable[Block]) -> None:
        self.content = content

    def dump(self, fp: TextIO):
        for block in self.content:
            block.print(fp)

# ## The Parser

# Finally, we have come to the core functionality of illiterate, the class
# that reads Python source code and produces the corresponding blocks.

# Since we don't really care about the structure of the code, this parser
# is very simple. Formally, we are dealing with a regular language, since
# we can determine what type of content we are dealing with based solely on the
# first character.
# Intuitively, as long as we are seeing either a `#` or blank lines, we are
# seeing Markdown. Once we see a line that doesn't begin with a `#`, that
# must be code.
# The parser is then a very simple automaton with two states. 

class Parser:
    def __init__(self, input_src: TextIO) -> None:
        self.input_src = input_src

    def parse(self):
        content = []
        current = []
        state = "markdown"

        for line in self.input_src:
            if line.startswith("#"):
                if state == "python":
                    if current:
                        content.append(Python(current))
                        current = []
                    state = "markdown"
                current.append(line)
            else:
                if state == "markdown":
                    if current:
                        content.append(Markdown(current))
                        current = []
                    state = "python"
                current.append(line)

        if current:
            if state == "markdown":
                content.append(Markdown(current))
            else:
                content.append(Python(current))

        return Content(*content)
