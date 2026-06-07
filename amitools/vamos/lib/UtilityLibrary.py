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
  
  def ToLower(self, ctx):
    a = ctx.cpu.r_reg(REG_D0) & 0xff
    return ord(chr(a).lower())

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

  def Date2Amiga(self, ctx):
    date_ptr = ctx.cpu.r_reg(REG_A0)
    clock = AccessStruct(ctx.mem,ClockDataDef,struct_addr=date_ptr)
    month = clock.r_s("month") + 9
    year  = clock.r_s("year") - 1 + month / 12
    month = month % 12
    month = month * 306 + 5
    date  = year * 365 + year / 4 - year / 100 + year / 400 + month / 10 + clock.r_s("mday") - 1 - 722390
    hour  = date * 24 + clock.r_s("hour")
    minute = hour * 60 + clock.r_s("minute")
    second = minute * 60 + clock.r_s("sec")
    ctx.cpu.w_reg(REG_D0,second)

  def Amiga2Date(self, ctx):
    date_ptr = ctx.cpu.r_reg(REG_A0)
    seconds = ctx.cpu.r_reg(REG_D0)
    clock = AccessStruct(ctx.mem,ClockDataDef,struct_addr=date_ptr)
    secs = seconds % 60
    minute = seconds / 60
    hour = minute / 60
    minute = minute % 60
    hour = hour % 24
    absday = seconds / (60 * 60 * 24) + 722390
    clock.w_s("wday",(absday + 3) % 7)
    work = absday - (absday + 1) / 146097
    work = work + work / 36524
    work = work - (work + 1) / 1461
    year = work / 365
    work = absday - year * 365 - year / 4 + year / 100 - year / 400
    month = (work / 153) * 5 + (10 * (work % 153)) / 305
    day = 1 + work - (month * 306 + 5) / 10
    month = month + 2
    year = year + month / 12
    month = month % 12 + 1
    clock.w_s("sec",secs)
    clock.w_s("minute",minute)
    clock.w_s("hour",hour)
    clock.w_s("mday",day)
    clock.w_s("month",month)
    clock.w_s("year",year)
