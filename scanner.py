"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""

import re


class Symbol:
  """Encapsulate a symbol and store its properties.

  Parameters
  ----------
  No parameters.

  Public methods
  --------------
  No public methods.
  """

  def __init__(self, type=None, id=None, loc=None):
    """Initialise symbol properties."""
    self.type = type
    self.id = id
    self.loc = loc


class Scanner:
  """Read circuit definition file and translate the characters into symbols.

  Once supplied with the path to a valid definition file, the scanner
  translates the sequence of characters in the definition file into symbols
  that the parser can use. It also skips over comments and irrelevant
  formatting characters, such as spaces and line breaks.

  Parameters
  ----------
  path: path to the circuit definition file.
  names: instance of the names.Names() class.

  Public methods
  -------------
  get_symbol(self): Translates the next sequence of characters into a symbol
                    and returns the symbol.
  """

  CLOCK = 0
  SWITCH = 1
  AND = 2
  OR = 3
  NAND = 4
  NOR = 5
  DTYPE = 6
  XOR = 7
  
  DOT = 8
  COMMA = 9
  OPEN = 10
  CLOSE = 11
  WHITESPACE = 12
  EQUALS = 13

  NAME = 14
  NUMBER = 15
  INVALID = 16
  EOL = 17
  EOF = 18

  MONITOR = 19

  def __init__(self, path, names):
    """Open specified file and initialise reserved words and IDs."""
    self.__path = path
    self.__names = names
    self.__done = False

    def symbol_gen():
      with open(path, 'r') as f:
        for line in f:
          loc = 0
          for w in re.split(r"(\.|,|\(|\)| +|=)", line):
            s = w.lower().strip()

            if s != "":
              type = self.get_symbol_type(s)
              [id] = self.__names.lookup([s])

              yield Symbol(type=type, id=id, loc=loc)

            loc += len(w)
          yield Symbol(type=self.EOL, loc=loc)
        yield Symbol(type=self.EOF)

    self.__symbols = symbol_gen()

  def get_line(self, number):
    line = None
    with open(self.__path, 'r') as f:
      for _ in range(number):
        line = next(f)
    return line.strip()
  
  def get_symbol_type(self, w):
    if w == "clk":
      return self.CLOCK
    if w == "sw":
      return self.SWITCH
    if w == "and":
      return self.AND
    if w == "or":
      return self.OR
    if w == "nand":
      return self.NAND
    if w == "nor":
      return self.NOR
    if w == "dtype":
      return self.DTYPE
    if w == "xor":
      return self.XOR
    if w == '.':
      return self.DOT
    if w == ',':
      return self.COMMA
    if w == '(':
      return self.OPEN
    if w == ')':
      return self.CLOSE
    if w == ' ':
      return self.WHITESPACE
    if w == '=':
      return self.EQUALS
    if w == '':
      return self.EOL
    if w == 'monitor':
      return self.MONITOR
    # if re.match(r"^[a-zA-Z_]{1}\w*$", w):
    #   return self.NAME
    if w.isdigit():
      return self.NUMBER
    return self.NAME

  def get_symbol(self):
    """Translate the next sequence of characters into a symbol."""
    return next(self.__symbols)
