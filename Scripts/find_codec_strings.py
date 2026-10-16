import re
b=open(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe','rb').read()
for m in re.finditer(rb'[ -~]{5,}',b):
 s=m.group().decode('latin1','ignore')
 if any(k in s.lower() for k in ['codec','quantiz','decompress','anim_raw','animstream','anim.*codec']): print(hex(m.start()),s[:200])
