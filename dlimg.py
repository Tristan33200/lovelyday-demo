import sys,os,re,hashlib,subprocess,concurrent.futures as cf
from PIL import Image
urls=[u for u in open('post_images.txt').read().split('\n') if u]
def name(u):
    b=os.path.basename(u.split('?')[0])
    b=re.sub(r'-\d+x\d+(?=\.\w+$)','',b); b=re.sub(r'-scaled(?=\.\w+$)','',b)
    stem=re.sub(r'\.\w+$','',b); stem=re.sub(r'[^A-Za-z0-9_-]+','-',stem)[:70]
    return stem+'-'+hashlib.md5(u.encode()).hexdigest()[:5]+'.webp'
def go(u):
    n=name(u); out='blogimg/'+n
    if os.path.exists(out): return u,n,'skip'
    tmp='blogdl/'+n+'.src'
    r=subprocess.run(['curl','-sSL','--max-time','60','-o',tmp,u])
    try:
        im=Image.open(tmp); im=im.convert('RGB'); im.thumbnail((1400,1400)); im.save(out,quality=72); os.remove(tmp); return u,n,'ok'
    except Exception as e: return u,n,'ERR '+str(e)[:60]
with cf.ThreadPoolExecutor(12) as ex:
    res=list(ex.map(go,urls))
open('img_map.tsv','w').write('\n'.join(f'{u}\t{n}\t{s}' for u,n,s in res))
print(sum(1 for r in res if r[2] in('ok','skip')),'ok', [r for r in res if r[2].startswith('ERR')][:5])
