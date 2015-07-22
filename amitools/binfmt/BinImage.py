
SEGMENT_TYPE_CODE = 0
SEGMENT_TYPE_DATA = 1
SEGMENT_TYPE_BSS = 2

SEGMENT_FLAG_READ_ONLY = 1

segment_type_names = [
  "CODE", "DATA", "BSS"
]

BIN_IMAGE_TYPE_HUNK = 0
BIN_IMAGE_TYPE_ELF = 1

bin_image_type_names = [
  "hunk", "elf"
]

class Reloc:
  def __init__(self, offset, width=2, addend=0):
    self.offset = offset
    self.width = width
    self.addend = addend

  def get_offset(self):
    return self.offset

  def get_width(self):
    return self.width

  def get_addend(self):
    return self.addend


class Relocations:
  def __init__(self, to_seg):
    self.to_seg = to_seg
    self.entries = []

  def add_reloc(self, reloc):
    self.entries.append(reloc)

  def get_relocs(self):
    return self.entries


class Symbol:
  def __init__(self, offset, name, file_name=None):
    self.offset = offset
    self.name = name
    self.file_name = file_name

  def get_offset(self):
    return self.offset

  def get_name(self):
    return self.name

  def get_file_name(self):
    return self.file_name


class SymbolTable:
  def __init__(self):
    self.symbols = []

  def add_symbol(self, symbol):
    self.symbols.append(symbol)

  def get_symbols(self):
    return self.symbols


class DebugLineEntry:
  def __init__(self, offset, src_line):
    self.offset = offset
    self.src_line = src_line

  def get_offset(self):
    return self.offset

  def get_src_line(self):
    return self.src_line


class DebugLine:
  def __init__(self):
    self.file_map = {}

  def add_file(self, src_file):
    self.file_map[src_file] = []

  def add_entry(self, src_file, offset, src_line):
    self.file_map[src_file].append(DebugLineEntry(offset, src_line))

  def get_src_files(self):
    return self.file_map.keys()

  def get_entries(self, src_file):
    return self.file_map[src_file]


class Segment:
  def __init__(self, seg_type, size, data=None, flags=0):
    self.seg_type = seg_type
    self.size = size
    self.data = data
    self.flags = flags
    self.relocs = {}
    self.symtab = None
    self.id = None
    self.file_data = None
    self.debug_line = None

  def __str__(self):
    # relocs
    relocs = []
    for to_seg in self.relocs:
      r = self.relocs[to_seg]
      relocs.append("(#%d:size=%d)" % (to_seg.id, len(r.entries)))
    # symtab
    if self.symtab is not None:
      symtab = "symtab=#%d" % len(self.symtab.symbols)
    else:
      symtab = ""
    # debug_line
    if self.debug_line is not None:
      src_files = self.debug_line.get_src_files()
      file_info = []
      for src_file in src_files:
        n = len(self.debug_line.get_entries(src_file))
        file_info.append("(%s:#%d)" % (src_file, n))
      debug_line = "debug_line=" + ",".join(file_info)
    else:
      debug_line = ""
    # summary
    return "[#%d:%s:size=%d,flags=%d,%s,%s,%s]" % (self.id,
      segment_type_names[self.seg_type], self.size, self.flags,
      ",".join(relocs), symtab, debug_line)

  def get_type(self):
    return self.seg_type

  def get_size(self):
    return self.size

  def get_data(self):
    return self.data

  def add_reloc(self, to_seg, relocs):
    self.relocs[to_seg] = relocs

  def get_reloc_to_segs(self):
    keys = self.relocs.keys()
    return sorted(keys, key=lambda x: x.id)

  def get_reloc(self, to_seg):
    return self.relocs[to_seg]

  def set_symtab(self, symtab):
    self.symtab = symtab

  def get_symtab(self):
    return self.symtab

  def set_debug_line(self, debug_line):
    self.debug_line = debug_line

  def get_debug_line(self):
    return self.debug_line

  def set_file_data(self, file_data):
    """set associated loaded binary file"""
    self.file_data = file_data

  def get_file_data(self):
    """get associated loaded binary file"""
    return self.file_data


class BinImage:
  """A binary image contains all the segments of a program's binary image.
  """
  def __init__(self, file_type):
    self.segments = []
    self.file_data = None
    self.file_type = file_type

  def __str__(self):
    return "<%s>" % ",".join(map(str,self.segments))

  def add_segment(self, seg):
    seg.id = len(self.segments)
    self.segments.append(seg)

  def get_segments(self):
    return self.segments

  def set_file_data(self, file_data):
    """set associated loaded binary file"""
    self.file_data = file_data

  def get_file_data(self):
    """get associated loaded binary file"""
    return self.file_data

