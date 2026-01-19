import polib
import os

# 编译 zh_CN 的 po 文件为 mo 文件
po_file = 'locale/zh_CN/LC_MESSAGES/pystart.po'
mo_file = 'locale/zh_CN/LC_MESSAGES/pystart.mo'

if os.path.exists(po_file):
    po = polib.pofile(po_file)
    po.save_as_mofile(mo_file)
    print(f"Compiled {po_file} to {mo_file}")
else:
    print(f"File {po_file} not found")