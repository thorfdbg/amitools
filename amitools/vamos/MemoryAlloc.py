from Exceptions import *
from Log import log_mem_alloc
from label.LabelRange import LabelRange
from label.LabelStruct import LabelStruct
from AccessStruct import AccessStruct
import sys

class Memory:
  def __init__(self, addr, size, label, access):
    self.addr = addr
    self.size = size
    self.label = label
    self.access = access
  def __str__(self):
    if self.label != None:
      return str(self.label)
    else:
      return "[@%06x +%06x %06x]" % (self.addr, self.size, self.addr+self.size)

# free memory chunk
class MemoryChunk:
  def __init__(self, addr, size):
    self.addr = addr
    self.size = size
    self.next = None
    self.prev = None

  def __str__(self):
    end = self.addr + self.size
    return "[@%06x +%06x %06x]" % (self.addr, self.size, end)

  def does_fit(self, size):
    """check if new size would fit into chunk
       return < 0 if it does not fit, 0 for exact fit, > 0 n wasted bytes
    """
    return self.size - size

class MemoryAlloc:
  def __init__(self, mem, addr, size, begin, label_mgr):
    self.addr = addr
    self.begin = begin
    self.size = size
    self.addrs = {}
    self.mem_objs = {}
    self.mem = mem
    self.access = mem.access
    self.label_mgr = label_mgr

    # init free list
    self.free_bytes = size - (begin - addr)
    self.free_first = MemoryChunk(begin, self.free_bytes)
    self.free_entries = 1
    #self.next_dump  = self.free_bytes - 0x10000

  def _find_best_chunk(self, size):
    """find best chunk that could take the given alloc
       return: index of chunk in free list or -1 if none found + bytes left in chunk
    """
    chunk = self.free_first
    while chunk != None:
      left = chunk.does_fit(size)
      # exact match
      if left == 0:
        return (chunk,0)
      # potential candidate: has some bytes left
      elif left > 0:
        # Don't make such a hassle. Return the first one that fits.
        # This function takes too much time.
        return (chunk,left)
      chunk = chunk.next
    # nothing found?
    return (None,-1)

  def _remove_chunk(self, chunk):
    next = chunk.next
    prev = chunk.prev
    if chunk == self.free_first:
      self.free_first = next
    if next != None:
      next.prev = prev
    if prev != None:
      prev.next = next
    self.free_entries -= 1

  def _replace_chunk(self, old_chunk, new_chunk):
    next = old_chunk.next
    prev = old_chunk.prev
    if old_chunk == self.free_first:
      self.free_first = new_chunk
    if next != None:
      next.prev = new_chunk
    if prev != None:
      prev.next = new_chunk
    new_chunk.next = next
    new_chunk.prev = prev

  def _insert_chunk(self, chunk):
    cur = self.free_first
    last = None
    addr = chunk.addr
    while cur != None:
      # fits right before
      if addr < cur.addr:
        break
      last = cur
      cur = cur.next
    # inster after last but before cur
    if last == None:
      self.free_first = chunk
    else:
      last.next = chunk
      chunk.prev = last
    if cur != None:
      chunk.next = cur
      cur.prev = chunk
    self.free_entries += 1

  def _merge_chunk(self, a, b):
    # can we merge?
    if a.addr + a.size == b.addr:
      chunk = MemoryChunk(a.addr, a.size + b.size)
      prev = a.prev
      if prev != None:
        prev.next = chunk
        chunk.prev = prev
      next = b.next
      if next != None:
        next.prev = chunk
        chunk.next = next
      if self.free_first == a:
        self.free_first = chunk
      self.free_entries -= 1
      return chunk
    else:
      return None

  def _stat_info(self):
    num_allocs = len(self.addrs)
    return "(free %06x #%d) (allocs #%d)" % (self.free_bytes, self.free_entries, num_allocs)

  def alloc_mem(self, size, except_on_fail = True):
    """allocate memory and return addr or 0 if no more memory"""
    # align size to 4 bytes
    size = (size + 3) & ~3
    # find best free chunk
    chunk, left = self._find_best_chunk(size)
    # out of memory?
    if chunk == None:
      if except_on_fail:
        self.dump_orphans()
        log_mem_alloc.error("[alloc: NO MEMORY for %06x bytes]" % size)
        raise VamosInternalError("[alloc: NO MEMORY for %06x bytes]" % size)
      return 0
    # remove chunk from free list
    # is something left?
    addr = chunk.addr
    if left == 0:
      self._remove_chunk(chunk)
    else:
      left_chunk = MemoryChunk(addr + size, left)
      self._replace_chunk(chunk, left_chunk)
    # add to valid allocs map
    self.addrs[addr] = size
    self.free_bytes -= size
    # erase memory
    self.mem.access.clear_data(addr, size, 0)
    log_mem_alloc.info("[alloc @%06x-%06x: %06x bytes] %s", addr, addr+size, size, self._stat_info())
    if addr % 4:
      raise VamosInternalError("Memory pool is invalid, return address not aligned by a long word");
    #if self.free_bytes < self.next_dump:
    #  self.next_dump -= 0x10000
    #  sys.stderr.write("\n\n**** Memory allocation dump ****\n");
    #  self.dump_orphans()
    return addr

  def alloc_vec(self, size, except_on_fail = True):
    """allocate memory in allocVec style, recording the size in the memory itself"""
    addr = self.alloc_mem(size + 4,except_on_fail)
    if addr != 0:
      self.mem.access.w32(addr, size)
      return addr+4
    return 0

  def free_mem(self, addr, size):
    # first check if its a right alloc
    if not self.addrs.has_key(addr):
      raise VamosInternalError("Invalid Free'd Memory at %06x" % addr)
    real_size = self.addrs[addr]
    # remove from valid allocs
    del self.addrs[addr]
    # create a new free chunk
    chunk = MemoryChunk(addr, real_size)
    self._insert_chunk(chunk)

    # try to merge with prev/next
    prev = chunk.prev
    if prev != None:
      new_chunk = self._merge_chunk(prev, chunk)
      if new_chunk != None:
        log_mem_alloc.debug("merged: %s + this=%s -> %s", prev, chunk, new_chunk)
        chunk = new_chunk
    next = chunk.next
    if next != None:
      new_chunk = self._merge_chunk(chunk, next)
      if new_chunk != None:
        log_mem_alloc.debug("merged: this=%s + %s -> %s", chunk, next, new_chunk)

    # correct free bytes
    self.free_bytes += size
    num_allocs = len(self.addrs)
    log_mem_alloc.info("[free  @%06x-%06x: %06x bytes] %s", addr, addr+size, size, self._stat_info())

  def free_vec(self, addr):
    if addr != 0:
      size = self.mem.access.r32(addr-4)
      self.free_mem(addr-4,size)
    
  def get_range_by_addr(self, addr):
    if self.addrs.has_key(addr):
      return self.addrs[addr]
    else:
      return None

  def dump_mem_state(self):
    chunk = self.free_first
    num = 0
    while chunk != None:
      log_mem_alloc.debug("dump #%02d: %s" % (num, chunk))
      num += 1
      chunk = chunk.next

  def _dump_orphan(self, addr, size):
    log_mem_alloc.warn("orphan: [@%06x +%06x %06x]" % (addr, size, addr+size))
    if self.label_mgr != None:
      labels = self.label_mgr.get_intersecting_labels(addr,size)
      for l in labels:
        log_mem_alloc.warn("-> %s",l)

  def dump_orphans(self):
    last = self.free_first
    # orphan at begin?
    if last.addr != self.begin:
      addr = self.begin
      size = last.addr - addr
      self._dump_orphan(addr, size)
    # walk along free list
    cur = last.next
    while cur != None:
      addr = last.addr + last.size
      size = cur.addr - addr
      self._dump_orphan(addr, size)
      last = cur
      cur = cur.next
    # orphan at end?
    addr = last.addr + last.size
    end  = self.addr + self.size
    if addr != end:
      self._dump_orphan(addr, end-addr)

  # ----- convenience functions with label creation -----

  def get_memory(self, addr):
    if self.mem_objs.has_key(addr):
      return self.mem_objs[addr]
    else:
      return None

  # memory
  def alloc_memory(self, name, size, add_label=True, except_on_failure = True):
    addr = self.alloc_mem(size, except_on_failure)
    if addr == 0:
      return None
    if add_label and self.label_mgr != None:
      label = LabelRange(name, addr, size)
      self.label_mgr.add_label(label)
    else:
      label = None
    mem = Memory(addr,size,label,self.mem.access)
    log_mem_alloc.info("alloc memory: %s",mem)
    self.mem_objs[addr] = mem
    return mem

  def alloc_vector(self, name, size, add_label=True, except_on_failure = True):
    addr = self.alloc_vec(size, except_on_failure)
    if addr == 0:
      return None
    if add_label and self.label_mgr != None:
      label = LabelRange(name, addr, size)
      self.label_mgr.add_label(label)
    else:
      label = None
    mem = Memory(addr,size,label,self.mem.access)
    log_mem_alloc.info("alloc memory: %s",mem)
    self.mem_objs[addr] = mem
    return mem

  def free_memory(self, mem):
    log_mem_alloc.info("free memory: %s",mem)
    if mem.label != None:
      self.label_mgr.remove_label(mem.label)
    self.free_mem(mem.addr, mem.size)
    del self.mem_objs[mem.addr]

  def free_vector(self, mem):
    log_mem_alloc.info("free vector: %s",mem)
    if mem.label != None:
      self.label_mgr.remove_label(mem.label)
    self.free_vec(mem.addr)
    del self.mem_objs[mem.addr]

  # struct
  def alloc_struct(self, name, struct):
    size = struct.get_size()
    addr = self.alloc_vec(size)
    if self.label_mgr != None:
      label = LabelStruct(name, addr, struct)
      self.label_mgr.add_label(label)
    else:
      label = None
    access = AccessStruct(self.mem, struct, addr)
    mem = Memory(addr,size,label,access)
    log_mem_alloc.info("alloc struct: %s",mem)
    self.mem_objs[addr] = mem
    return mem

  def map_struct(self, name, addr, struct):
    size = struct.get_size()
    access = AccessStruct(self.mem, struct, addr)
    if self.label_mgr != None:
      label = self.label_mgr.get_label(addr)
    else:
      label = None
    mem = Memory(addr,size,label,access)
    log_mem_alloc.info("map struct: %s",mem)
    return mem

  def free_struct(self, mem):
    log_mem_alloc.info("free struct: %s",mem)
    if self.label_mgr != None:
      self.label_mgr.remove_label(mem.label)
    self.free_vec(mem.addr)
    del self.mem_objs[mem.addr]

  # cstr
  def alloc_cstr(self, name, cstr):
    size = len(cstr) + 1
    addr = self.alloc_mem(size)
    if self.label_mgr != None:
      label = LabelRange(name, addr, size)
      self.label_mgr.add_label(label)
    else:
      label = None
    self.mem.access.w_cstr(addr, cstr)
    mem = Memory(addr,size,label,self.mem.access)
    log_mem_alloc.info("alloc c_str: %s",mem)
    self.mem_objs[addr] = mem
    return mem

  def free_cstr(self, mem):
    log_mem_alloc.info("free c_str: %s",mem)
    if self.label_mgr != None:
      self.label_mgr.remove_label(mem.label)
    self.free_mem(mem.addr, mem.size)
    del self.mem_objs[mem.addr]

  # bstr
  def alloc_bstr(self, name, bstr):
    size = len(bstr) + 2 # front: count, end: extra zero for safety
    addr = self.alloc_mem(size)
    if self.label_mgr != None:
      label = LabelRange(name, addr, size)
      self.label_mgr.add_label(label)
    else:
      label = None
    self.mem.access.w_bstr(addr, bstr)
    mem = Memory(addr,size,label,self.mem.access)
    log_mem_alloc.info("alloc b_str: %s",mem)
    self.mem_objs[addr] = mem
    return mem

  def free_bstr(self, mem):
    log_mem_alloc.info("free b_str: %s",mem)
    if self.label_mgr != None:
      self.label_mgr.remove_label(mem.label)
    self.free_mem(mem.addr, mem.size)
    del self.mem_objs[mem.addr]

  def is_valid_address(self, addr):
    if addr >= self.begin and addr < self.begin + self.size:
      return True
    return False

  def total(self):
    return self.size

  def available(self):
    free  = 0
    chunk = self.free_first
    while chunk != None:
      free += chunk.size
      chunk = chunk.next
    return free

  def largest_chunk(self):
    largest = 0
    chunk = self.free_first
    while chunk != None:
      if chunk.size > largest:
        largest = chunk.size
      chunk = chunk.next
    return largest


