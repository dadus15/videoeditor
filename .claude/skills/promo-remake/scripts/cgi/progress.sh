#!/usr/bin/env bash
# Render progress: frames done / total, per shot, and an ETA from the last 10 frames.
cd "$(dirname "$0")/.."
RES=${1:-720}
python3 - "$RES" <<'PY'
import sys, time, re
from pathlib import Path
sys.argv=[sys.argv[0]]+sys.argv[1:]
src=Path('cgi/shots.py').read_text()
shots=re.findall(r'^\s+"(\w+)": dict\(frames=(\d+)', src, re.M)
root=Path('work/cgi')/sys.argv[1]
total=sum(int(n) for _,n in shots); done=0; files=[]
rows=[]
for name,n in shots:
    fs=sorted((root/name).glob('f*.png')) if (root/name).exists() else []
    k=min(len(fs),int(n)); done+=k; files+=fs
    rows.append((name,k,int(n)))
pct=100*done/total
bar='█'*int(pct/4)+'░'*(25-int(pct/4))
times=sorted(f.stat().st_mtime for f in files)[-11:]
eta=''
if len(times)>=2:
    spf=(times[-1]-times[0])/(len(times)-1)
    left=(total-done)*spf
    eta=f'  ~{spf:.0f} s/klatkę, zostało ok. {int(left//3600)} h {int(left%3600//60)} min'
print(f'[{bar}] {pct:5.1f}%  {done}/{total} klatek{eta}')
cur=[r for r in rows if 0<r[1]<r[2]] or [r for r in rows if r[1]==0][:1]
print('teraz: '+', '.join(f'{a} {b}/{c}' for a,b,c in cur) + '   gotowe ujęcia: ' + str(sum(1 for r in rows if r[1]>=r[2]))+'/'+str(len(rows)))
PY
