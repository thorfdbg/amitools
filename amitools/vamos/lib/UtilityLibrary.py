from amitools.vamos.AmigaLibrary import *
from amitools.vamos.lib.lexec.ExecStruct import LibraryDef
from amitools.vamos.Log import *
from amitools.vamos.AccessStruct import AccessStruct
from util.UtilStruct import *
from util.TagList import *


class UtilityLibrary(AmigaLibrary):
  name = "utility.library"

  def __init__(self, config):
    AmigaLibrary.__init__(self, self.name, LibraryDef, config)

  def setup_lib(self, ctx):
    AmigaLibrary.setup_lib(self, ctx)

  def UDivMod32(self, ctx):
    dividend = ctx.cpu.r_reg(REG_D0)
    divisor = ctx.cpu.r_reg(REG_D1)
    quot = dividend / divisor
    rem  = dividend % divisor
    log_utility.info("UDivMod32(dividend=%u, divisor=%u) => (quotient=%u, remainder=%u)" % (dividend, divisor, quot, rem))
    return [quot, rem]
  
  def SDivMod32(self, ctx):
    dividend = ctx.cpu.r_reg(REG_D0)
    if dividend >= 0x80000000:
      dividend = dividend - 0x100000000
    divisor = ctx.cpu.r_reg(REG_D1)
    if divisor >= 0x80000000:
      divisor = divisor - 0x100000000
    quot = dividend / divisor
    rem  = dividend % divisor
    if quot < 0:
      quot = quot + 0x100000000
    if rem < 0:
      rem = rem + 0x100000000
    log_utility.info("UDivMod32(dividend=%u, divisor=%u) => (quotient=%u, remainder=%u)" % (dividend, divisor, quot, rem))
    return [quot, rem]

  def UMult32(self, ctx):
    a = ctx.cpu.r_reg(REG_D0)
    b = ctx.cpu.r_reg(REG_D1)
    c = (a * b) & 0xffffffff
    log_utility.info("UMult32(a=%u, b=%u) => %u", a, b, c)
    return c

  def SMult32(self, ctx):
    # Z_{2^32} is a ring. It does not matter whether we multiply signed or unsigned
    a = ctx.cpu.r_reg(REG_D0)
    b = ctx.cpu.r_reg(REG_D1)
    c = (a * b) & 0xffffffff
    log_utility.info("SMult32(a=%d, b=%d) => %d", a, b, c)
    return c

  def ToUpper(self, ctx):
    a = ctx.cpu.r_reg(REG_D0) & 0xff
    return ord(chr(a).upper())

  def Stricmp(self, ctx):
    str1_addr = ctx.cpu.r_reg(REG_A0)
    str2_addr = ctx.cpu.r_reg(REG_A1)
    str1 = ctx.mem.access.r_cstr(str1_addr)
    str2 = ctx.mem.access.r_cstr(str2_addr)
    log_utility.info("Stricmp(%08x=\"%s\",%08x=\"%s\")" % (str1_addr,str1,str2_addr,str2))
    if str1.lower() < str2.lower():
      return -1
    elif str1.lower() > str2.lower():
      return +1
    else:
      return 0

  def Strnicmp(self, ctx):
    str1_addr = ctx.cpu.r_reg(REG_A0)
    str2_addr = ctx.cpu.r_reg(REG_A1)
    length    = ctx.cpu.r_reg(REG_D0)
    str1 = ctx.mem.access.r_cstr(str1_addr)[:length]
    str2 = ctx.mem.access.r_cstr(str2_addr)[:length]
    log_utility.info("Strnicmp(%08x=\"%s\",%08x=\"%s\")" % (str1_addr,str1,str2_addr,str2))
    if str1.lower() < str2.lower():
      return -1
    elif str1.lower() > str2.lower():
      return +1
    else:
      return 0

  def CallHookPkt(self, ctx):
    hk_ptr = ctx.cpu.r_reg(REG_A0)
    hook = AccessStruct(ctx.mem,HookDef,struct_addr=hk_ptr)
    func = hook.r_s("h_Entry")
    log_utility.info("CallHookPkt(0x%08x) call 0x%08x" % (hk_ptr,func))
    old_stack = ctx.cpu.r_reg(REG_A7)
    old_pc    = ctx.cpu.r_reg(REG_PC)
    new_stack = old_stack - 4
    ctx.cpu.w_reg(REG_A7, new_stack)
    ctx.mem.access.w32(new_stack, func)

  def FilterTagItems(self, ctx):
    taglist_ptr = ctx.cpu.r_reg(REG_A0)
    filter_ptr  = ctx.cpu.r_reg(REG_A1)
    logic       = ctx.cpu.r_reg(REG_D0)
    nvalid      = 0
    while True:
      tag = ctx.mem.access.r32(taglist_ptr)
      if tag == TAG_DONE:
        break
      elif tag == TAG_IGNORE:
        taglist_ptr += 8
      elif tag == TAG_SKIP:
        skip_count   = ctx.mem.access.r32(taglist_ptr + 4)
        taglist_ptr += 8 + 8 * skip_count
      elif tag == TAG_MORE:
        taglist_ptr = ctx.mem.access.r32(taglist_ptr + 4)
      else:
        filt = filter_ptr
        while True:
          ftag = ctx.mem.access.r32(filt)
          if ftag == TAG_DONE:
            break
          if ftag == tag:
            break
          filt += 4
        if (ftag == tag and logic == 0) or (ftag != tag and logic != 0):
            nvalid += 1
        else:
            ctxt.mem.access.w32(taglist_ptr,TAG_IGNORE)
        taglist_ptr += 8
    log_utility.info("FilterTagItems(0x%08x,0x%08lx,%d) -> %d" % (taglist_ptr,filter_ptr,logic,nvalid))
    return nvalid
