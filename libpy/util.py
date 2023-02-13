import os

################################
# Utilities
################################

class Reader:
    def __init__(self, str):
        self.str = str
        self.idx = 0

    def current(self):
        if self.idx < 0 or self.idx >= len(self.str):
            return None
        return self.str[self.idx]

    def next(self, amt = 1):
        self.idx += amt
        if self.idx < 0 or self.idx >= len(self.str):
            return None
        return self.str[self.idx]

    def prev(self, amt = 1):
        self.idx -= amt
        if self.idx < 0 or self.idx >= len(self.str):
            return None
        return self.str[self.idx]

    def peek(self, off):
        idx = self.idx + off
        if idx >= len(self.str) or idx < 0:
            return None
        return self.str[idx]

    def at(self, index):
        if index > 0:
            return self.str[index]
        else:
            idx = self.idx - abs(index)
            if idx >= len(self.str) or idx < 0:
                return None
            return self.str[idx]

    def collect(self, pred):
        str = ""
        while self.current() != None and pred(self.current()):
            str += self.current()
            self.next()
        return str

    def pcollect(self, pred):
        while self.current() != None and pred(self.current()):
            self.next()
        return str

# check if the given char is a path sep
def is_path_sep(char):
    return char == '\\' or char == '/'

# fixes the given path and replaces
# placeholders in it
def fix_path(pstr):
    seg      = ""
    segments = []
    reader = Reader(pstr)
    char   = reader.current()
    while char != None:
        # check for separator
        if is_path_sep(char):
            if len(seg) > 2 and seg[0] == '%':
                seg = os.getenv(seg[1:-1])
            segments.append(seg)
            seg = ""
        else:
            seg += char

        char = reader.next()

    # stitch to string
    result = ""
    for segment in segments:
        result += segment + "/"
    return result

# get index by position/offset
# into a list of length len
def get_idx_by_pos(len, pos):
    if pos < 0:
        return len + pos
    else:
        return pos
    
def flat_concat(list):
    rstr = ""
    l = len(list)
    for i in range(0, l):
        rstr += str(list[i])
        if i < l - 1:
            rstr += ", "
    return rstr

#
# from: https://stackoverflow.com/questions/2020014/get-fully-qualified-class-name-of-an-object-in-python
#
def full_type_name(klass):
    module = klass.__module__
    if module == 'builtins':
        return klass.__qualname__ # avoid outputs like 'builtins.str'
    return module + '.' + klass.__qualname__

def replace_placeholders(istr: str, vals: dict):
    reader = Reader(istr)
    ostr = ""
    while reader.current():
        # check for placeholder
        if reader.current() == '$' and reader.peek(1) == '{':
            reader.next(2)

            # collect name
            name = reader.collect(lambda c : c != '}')
            reader.next() # close brackets

            # replace name
            val = None
            if name in vals:
                val = vals[name]
            ostr += str(val)
        else:
            # append char
            ostr += reader.current()
            reader.next()
    return ostr