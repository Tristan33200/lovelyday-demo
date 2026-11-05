import sys,os,re,glob
from PIL import Image
sys.path.insert(0,'.')
import importlib.util
src=open('dlimg.py').read().split('def go')[0].replace("urls=[u for u in open('post_images.txt').read().split('\\n') if u]","")
ns={};exec(src,ns);name=ns['name']
m={l.split('\t')[0] for l in open('img_map.tsv') if l.strip()}
urls=[u.strip() for u in open('drafts/imgs.txt') if u.strip()]
files={}
for d in sys.argv[1:]:
    for f in glob.glob(d+'/*'):
        b=os.path.basename(f)
        if '.bk.' in b: continue
        files.setdefault(b.lower(),[]).append(f)
def norm(b):
    b=re.sub(r'-\d+x\d+(?=\.\w+$)','',b); return re.sub(r'-scaled(?=\.\w+$)','',b).lower()
bystem={}
for b,fs in files.items(): bystem.setdefault(norm(b),[]).extend(fs)
added=[];miss=[]
for u in urls:
    if u in m: continue
    key=norm(os.path.basename(u.split('?')[0]))
    c=bystem.get(key)
    if not c: miss.append(u); continue
    best=max(c,key=os.path.getsize)
    n=name(u); out='blogimg/'+n
    if not os.path.exists(out):
        im=Image.open(best).convert('RGB'); im.thumbnail((1400,1400)); im.save(out,quality=72)
    added.append(f'{u}\t{n}\tok')
with open('img_map.tsv','a') as fh:
    for a in added: fh.write('\n'+a)
print(len(added),'ajoutées;',len(miss),'manquantes'); [print(' ',x) for x in miss]
