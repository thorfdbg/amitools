from amitools.vamos.AmigaLibrary import *
from amitools.vamos.lib.lexec.ExecStruct import LibraryDef
from amitools.vamos.Log import *
import struct
import math


def fromSingle(number):
  lo=0
  st=struct.pack('>f',number)
  for c in st[0:4]:
    lo=(lo << 8) | ord(c)
  return lo

def toSingle(lo):
  st=""
  for i in range(0,4):
    st=st+chr(lo >> 24)
    lo=(lo << 8) & 0xffffffff
  return struct.unpack('>f',st)[0]

class MathIEEESingBasLibrary(AmigaLibrary):
  name = "mathieeesingbas.library"

  def __init__(self, config):
    AmigaLibrary.__init__(self, self.name, LibraryDef, config)

  def setup_lib(self, ctx):
    AmigaLibrary.setup_lib(self, ctx)

  def IEEEDPFix(self, ctx):
    arg=toSingle(ctx.cpu.r_reg(REG_D0))
    return int(arg)

  def IEEEFlt(self, ctx):
    lo=fromSingle(ctx.cpu.r_reg(REG_D0)+0.0)
    return lo

  def IEEEDPCmp(self, ctx):
    arg1=toSingle(ctx.cpu.r_reg(REG_D0))
    arg2=toSingle(ctx.cpu.r_reg(REG_D1))
    if arg1<arg2:
      return -1
    elif arg1>arg2:
      return +1
    else:
      return 0
    
  def IEEEDPTst(self,ctx):
    arg1=toSingle(ctx.cpu.r_reg(REG_D0))
    if arg1<0.0:
      return -1
    elif arg1>0.0:
      return +1
    else:
      return 0

  def IEEEDPAbs(self,ctx):
    arg1=toSingle(ctx.cpu.r_reg(REG_D0))
    if arg1<0:
      arg1=-arg1
    lo=fromSingle(arg1)
    return lo

  def IEEEDPAdd(self,ctx):
    arg1=toSingle(ctx.cpu.r_reg(REG_D0))
    arg2=toSingle(ctx.cpu.r_reg(REG_D1))
    lo=fromSingle(arg1+arg2)
    return lo

  def IEEEDPSub(self,ctx):
    arg1=toSingle(ctx.cpu.r_reg(REG_D0))
    arg2=toSingle(ctx.cpu.r_reg(REG_D1))
    lo=fromSingle(arg1-arg2)
    return lo
  
  def IEEEDPMul(self,ctx):
    arg1=toSingle(ctx.cpu.r_reg(REG_D0))
    arg2=toSingle(ctx.cpu.r_reg(REG_D1))
    lo=fromSingle(arg1*arg2)
    return lo
  
  def IEEEDPDiv(self,ctx):
    arg1=toSingle(ctx.cpu.r_reg(REG_D0))
    arg2=toSingle(ctx.cpu.r_reg(REG_D1))
    lo=fromSingle(arg1/arg2)
    return lo
  
  def IEEEDPFloor(self,ctx):
    arg1=toSingle(ctx.cpu.r_reg(REG_D0))
    lo=fromSingle(math.floor(arg1))
    return lo
  
  def IEEEDPCeil(self,ctx):
    arg1=toSingle(ctx.cpu.r_reg(REG_D0))
    lo=fromSingle(math.ceil(arg1))
    return lo

