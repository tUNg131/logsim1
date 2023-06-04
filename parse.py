"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""
import itertools

from scanner import Scanner

class ParsingError(Exception):
  def __init__(self, message, sym=None):
    self.message = message
    self.sym = sym


class Parser:

  """Parse the definition file and build the logic network.

  The parser deals with error handling. It analyses the syntactic and
  semantic correctness of the symbols it receives from the scanner, and
  then builds the logic network. If there are errors in the definition file,
  the parser detects this and tries to recover from it, giving helpful
  error messages.

  Parameters
  ----------
  names: instance of the names.Names() class.
  devices: instance of the devices.Devices() class.
  network: instance of the network.Network() class.
  monitors: instance of the monitors.Monitors() class.
  scanner: instance of the scanner.Scanner() class.

  Public methods
  --------------
  parse_network(self): Parses the circuit definition file.
  """

  def __init__(self, names, devices, network, monitors, scanner):
    """Initialise constants."""
    self.__names = names
    self.__devices = devices
    self.__network = network
    self.__monitors = monitors
    self.__scanner: Scanner = scanner

  def parse_network(self):
    """Parse the circuit definition file."""
    line_count = 1
    try:
      while True:
        sym = self.__scanner.get_symbol()

        if sym.type == Scanner.EOF:
          break

        if sym.type == Scanner.AND:
          self._parse_AND()
        elif sym.type == Scanner.NAND:
          self._parse_NAND()
        elif sym.type == Scanner.OR:
          self._parse_OR()
        elif sym.type == Scanner.NOR:
          self._parse_NOR()
        elif sym.type == Scanner.XOR:
          self._parse_XOR()
        elif sym.type == Scanner.CLOCK:
          self._parse_CLOCK()
        elif sym.type == Scanner.DTYPE:
          self._parse_DTYPE()
        elif sym.type == Scanner.SWITCH:
          self._parse_SWITCH()
        elif sym.type == Scanner.MONITOR:
          self._parse_monitor()
        elif sym.type == Scanner.NAME:
          self._parse_connection(sym)

        line_count += 1
    except ParsingError as e:
      print(e.message)
      print()
      print(f"{line_count} ", self.__scanner.get_line(line_count))
      if e.sym:
        print(" "*len(f"{line_count} "), " " * e.sym.loc + "^")
      return False
    return True

  def multiple(parse):
    def wrapper(self, *args, **kwargs):
      parse(self, *args, **kwargs)

      while True:
        sym = self.__scanner.get_symbol()
        if sym.type == Scanner.EOL:
          break

        # ,
        if sym.type != Scanner.COMMA:
          raise ParsingError("Expecting ','", sym=sym)

        parse(self, *args, **kwargs)
    return wrapper

  def _parse_identifier(self):
    sym = self.__scanner.get_symbol()
    if sym.type != Scanner.NAME:
      raise ParsingError(f"Expecting user-defined name", sym=sym)
    return sym.id

  def _parse_output(self):
    device_id = self._parse_identifier()
    port_id = None

    device = self.__devices.get_device(device_id)
    if device is None:
      raise ParsingError("Undeclared device")

    if device.device_kind == self.__devices.D_TYPE:
      self._parse_dot()
      port_id = self._parse_identifier()

    return device_id, port_id

  def _parse_open_bracket(self):
    sym = self.__scanner.get_symbol()
    if sym.type != Scanner.OPEN:
      raise ParsingError("Expecting open bracket", sym=sym)

  def _parse_close_bracket(self):
    sym = self.__scanner.get_symbol()
    if sym.type != Scanner.CLOSE:
      raise ParsingError("Expecting close bracket", sym=sym)

  def _parse_dot(self):
    sym = self.__scanner.get_symbol()
    if sym.type != Scanner.DOT:
      raise ParsingError("Expecting '.'", sym=sym)

  def _parse_gate(self, **kwargs):
    device_id = self._parse_identifier()

    # Default to XOR: 2 inputs
    no_of_inputs = 2

    if kwargs["device_kind"] != self.__devices.XOR:
      self._parse_open_bracket()

      class InvalidNoOfInputs(ValueError): pass
      try:
        # no_of_inputs
        sym = self.__scanner.get_symbol()
        if sym.type != Scanner.NUMBER:
          raise InvalidNoOfInputs
        
        number = self.__names.get_name_string(sym.id)

        if number[0] == "0":
          raise InvalidNoOfInputs

        no_of_inputs = int(number)

        if no_of_inputs > 16 or no_of_inputs < 1:
          raise ParsingError("Expecting a number from 1-16", sym=sym)
      except InvalidNoOfInputs:
        raise ParsingError("Expecting a number > 0", sym=sym)

      self._parse_close_bracket()

    kwargs.update(dict(device_id=device_id, no_of_inputs=no_of_inputs))

    self.__devices.make_gate(**kwargs)

  @multiple
  def _parse_AND(self):
    self._parse_gate(device_kind=self.__devices.AND)

  @multiple
  def _parse_OR(self):
    self._parse_gate(device_kind=self.__devices.OR)

  @multiple
  def _parse_NAND(self):
    self._parse_gate(device_kind=self.__devices.NAND)

  @multiple
  def _parse_NOR(self):
    self._parse_gate(device_kind=self.__devices.NOR)

  @multiple
  def _parse_XOR(self):
    self._parse_gate(device_kind=self.__devices.XOR)

  @multiple
  def _parse_CLOCK(self):
    device_id = self._parse_identifier()

    self._parse_open_bracket()

    class InvalidHalfPeriod(ValueError): pass

    try:
      # n
      sym = self.__scanner.get_symbol()
      if sym.type != Scanner.NUMBER:
        raise InvalidHalfPeriod
      
      name_string = self.__names.get_name_string(sym.id)

      if name_string[0] == "0":
        raise InvalidHalfPeriod

      clock_half_period = int(name_string)

      if clock_half_period < 1:
        raise InvalidHalfPeriod

    except InvalidHalfPeriod:
      raise ParsingError("Expecting a number > 0", sym=sym)

    self._parse_close_bracket()

    self.__devices.make_clock(device_id=device_id, clock_half_period=clock_half_period)

  @multiple
  def _parse_SWITCH(self):
    device_id = self._parse_identifier()

    self._parse_open_bracket()

    class InvalidState(ValueError): pass

    try:
      # initial state
      sym = self.__scanner.get_symbol()
      if sym.type != Scanner.NUMBER:
        raise InvalidState
      
      initial_state = int(self.__names.get_name_string(sym.id))

      if initial_state not in [0, 1]:
        raise InvalidState

    except InvalidState:
      raise ParsingError("Expecting 0 or 1", sym=sym)

    self._parse_close_bracket()

    self.__devices.make_switch(device_id=device_id,
                               initial_state=initial_state)

  @multiple
  def _parse_DTYPE(self):
    device_id = self._parse_identifier()

    self.__devices.make_dtype(device_id=device_id)

  @multiple
  def _parse_monitor(self):
    device_id, output_id = self._parse_output()

    error_code = self.__monitors.make_monitor(device_id=device_id,
                                              output_id=output_id)

    if error_code == self.__network.DEVICE_ABSENT:
      raise ParsingError("Undeclared device")
    elif error_code == self.__monitors.NOT_OUTPUT:
      raise ParsingError("Not monitoring output")
    elif error_code == self.__monitors.MONITOR_PRESENT:
      raise ParsingError("Monitor present")

  def _parse_connection(self, sym):
    args = [sym.id, None, None, None]

    def parse_right():
      # second_device
      args[2] = self._parse_identifier()

      sym = self.__scanner.get_symbol()

      if sym.type == Scanner.EOL:
        return

      if sym.type != Scanner.DOT:
        raise ParsingError("Expecting '.'", sym=sym)

      # second_port_id
      args[3] = self._parse_identifier()

      sym = self.__scanner.get_symbol()
      if sym.type != Scanner.EOL:
        raise ParsingError("Expecting EOL", sym=sym)

    sym = self.__scanner.get_symbol()
    if sym.type == Scanner.EQUALS:
      parse_right()
    elif sym.type == Scanner.DOT:
      # first_port
      sym = self.__scanner.get_symbol()
      if sym.type != Scanner.NAME:
        raise ParsingError("Expecting port name", sym=sym)

      args[1] = sym.id

      # =
      sym = self.__scanner.get_symbol()
      if sym.type != Scanner.EQUALS:
        raise ParsingError("Expecting '='", sym=sym)

      parse_right()
    else:
      raise ParsingError("Expecting . or =", sym=sym)

    error_code = self.__network.make_connection(*args)

    if error_code != self.__network.NO_ERROR:
      raise ParsingError("Network error")