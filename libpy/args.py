from libpy.util import *

################################
# CLI
################################

def stitch_args(argv):
    str = ""
    l = len(argv)
    for i in range(1, l):
        arg = argv[i]
        if " " in arg:
            str += "\"" + argv[i] + "\" "
        else:
            str += argv[i] + " "
    return str

# the pos value to signal the argument
# should be appended to the end
POS_APPEND_BACK = 0xFFFFFFFF

class ArgError(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

# simple arg repr
class Arg:
    # create a simple named arg
    def new(name: str, char: str, ty: type):
        return Arg(name, char, ty, None, None)
    # create a simple positional arg
    def new_positional(name: str, ty: type):
        return Arg(name, None, ty, None, POS_APPEND_BACK)
    # create a positional arg at the specified idx/pos
    def new_positional_at(name: str, ty: type, pos: int):
        return Arg(name, None, ty, None, pos)
    # create a switch arg
    def new_switch(name: str, char: str, ty: type, switch_handler):
        return Arg(name, char, ty, switch_handler, None)
    # create a boolean switch arg
    def new_bool_switch(name: str, char: str):
        return Arg.new_switch(name, char, bool, lambda *_ : True)

    def __init__(self, name: str, char: str, ty: type, sw_handler, pos: int):
        self.name       = name
        self.char       = char
        self.ty         = ty
        self.sw_handler = sw_handler
        self.pos        = pos
        self.defv       = None

    def default(self, val):
        self.defv = val
        return self

# a parser for a type
class TypeParser:
    def __init__(self, ty: type, pfunc):
        self.ty = ty
        self.pfunc = pfunc

    # abstract: parses the type
    def parse(self, parser, arg: Arg, reader: Reader):
        return self.pfunc(parser, arg, reader)
    
## Default Types ##

def _parse_str(_1, _2, reader: Reader):
    sc = reader.current()
    if sc == '\'' or sc == "\"":
        str = ""
        reader.next()
        while reader.current() and reader.current() != sc:
            c = reader.current()
            if c == '\\':
                str += reader.next()
                reader.next()
                continue
            str += c
            reader.next()
        reader.next()
        return str
    else:
        return reader.collect(lambda c : not c.isspace())
    
def _parse_bool(_1, _2, reader: Reader):
    if reader.current() == '1':
        return True
    elif reader.current() == '0':
        return False
    str = reader.collect(lambda c : not c.isspace())
    if str == 'true':
        return True
    return False
    
def define_default_types(parser):
    parser.define_type(TypeParser(int,   lambda _1, _2, reader : int(reader.collect(lambda c : c.isdigit() or c == '-'))))
    parser.define_type(TypeParser(float, lambda _1, _2, reader : float(reader.collect(lambda c : c.isdigit() or c == '-' or c == '.'))))
    parser.define_type(TypeParser(str,   _parse_str))
    parser.define_type(TypeParser(bool,  _parse_bool))

# arg parser
class ArgParser:
    def __init__(self):
        self.arg_map  = { } # args by name
        self.pos_args = [ ] # positioned list of args
        self.by_char  = { } # args by char
        self.types    = { } # type parsers

        define_default_types(self)

    def define_type(self, ty: TypeParser):
        self.types[ty.ty] = ty

    def get_type(self, ty: type):
        if not ty in self.types:
            raise ArgError("no type parser defined for " + str(ty))
        return self.types[ty]

    def add(self, arg: Arg):
        self.arg_map[arg.name] = arg
        if arg.char != None:
            self.by_char[arg.char] = arg
        if arg.pos != None:
            if arg.pos == POS_APPEND_BACK:
                self.pos_args.append(arg)
            else:
                self.pos_args.insert(get_idx_by_pos(len(self.pos_args), arg.pos), arg)

    def parse_val(self, arg: Arg, reader: Reader):
        try:
            return self.get_type(arg.ty).parse(self, arg, reader)
        except ArgError as e:
            print("arg: error occured parsing " + arg.name + ": " + e)
            raise ArgError("arg parse failed")
        
    def parse_errexit(self, arg_str: str, out: dict = None):
        try:
            return self.parse(arg_str, out=out)
        except ArgError as e:
            print(full_type_name(e.__class__) + ": " + flat_concat(e.args))
            os._exit(-1)

    def parse(self, arg_str: str, out: dict = None):
        if not out:
            out = { }

        pIdx = 0 # positional arg index
        reader = Reader(arg_str) # string reader
        c = None # char

        while reader.current() != None:
            # collect whitespace
            reader.pcollect(lambda c : c.isspace())

            c = reader.current()
            if not c:
                break

            # check for flags
            if c == '-':
                # check for named
                if reader.next() == '-':
                    # collect name
                    reader.next()
                    name = reader.collect(lambda c : c != ' ' and c != '=')

                    if not name in self.arg_map:
                        raise ArgError("unknown arg by name " + name)
                    arg = self.arg_map[name]

                    # check for explicit value
                    # or spaced value
                    # otherwise handle switch
                    val = None
                    if not arg.sw_handler or reader.current() == '=':
                        reader.next()
                        val = self.parse_val(arg, reader)
                    else: # switch
                        val = arg.sw_handler(self, arg)

                    # put val
                    out[arg.name] = val
                else:
                    while reader.current() != None and reader.current() != ' ':
                        if not reader.current() in self.by_char:
                            raise ArgError("unknown arg by char '" + reader.current() + "'")
                        arg = self.by_char[reader.current()]

                        # check switch
                        if not arg.sw_handler:
                            reader.next()
                            val = self.parse_val(arg, reader)
                            out[arg.name] = val
                            break
                        else:
                            out[arg.name] = arg.sw_handler(self, arg)
                            reader.next()
            else:
                # handle positional arg
                if pIdx >= len(self.pos_args):
                    raise ArgError("unexpected positional argument " + str(pIdx))
                arg = self.pos_args[pIdx]
                pIdx += 1
                val = self.parse_val(arg, reader)
                out[arg.name] = val

        # set default values for all unset args
        for arg in self.arg_map.values():
            if not arg.name in out and arg.defv:
                out[arg.name] = arg.defv

        return out