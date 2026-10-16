import re,sys
b=open(sys.argv[1],'rb').read()
for start in [38000,40000,41000,42000,42500,43000,43500,44000,44500,45000,45500,46000,46500,47000,47500,48000,48500,49000,49500,50000,50500,51000]:
 print('\n---',start,'---')
 for m in re.finditer(rb'[ -~]{3,}',b[start:start+1500]):
  s=m.group().decode('latin1','replace');
  print(start+m.start(),repr(s[:250]))
