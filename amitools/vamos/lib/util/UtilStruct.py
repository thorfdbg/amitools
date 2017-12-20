from amitools.vamos.AmigaStruct import AmigaStruct

# TagItem
class TagItemStruct(AmigaStruct):
  _name = "TagItem"
  _format = [
    ('ULONG','ti_Tag'),
    ('ULONG','ti_Data')
  ]
TagItemDef = TagItemStruct()

class HookStruct(AmigaStruct):
  _name = "Hook"
  _format = [
    ('MinNode','h_MinNode'),
    ('APTR','h_Entry'),
    ('APTR','h_SubEntry'),
    ('APTR','h_Data')
    ]
HookDef = HookStruct()
