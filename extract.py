import sys,bs4,re
for f in sys.argv[1:]:
    s=bs4.BeautifulSoup(open(f,encoding='utf-8'),'html.parser')
    for t in s(['script','style','noscript','svg']): t.decompose()
    m=s.find('main') or s.find(id='content') or s.body
    for t in m.find_all(['header','footer','nav']): t.decompose()
    print('=====',f)
    txt=m.get_text('\n',strip=True)
    print(re.sub(r'\n{2,}','\n',txt)[:9000])
    imgs=set()
    for i in m.find_all('img'):
        u=i.get('data-src') or i.get('src') or ''
        if 'uploads' in u: imgs.add(u)
    for i in re.findall(r'url\((["\']?)(https://lovelydayevent\.fr/wp-content/uploads[^)"\']+)',str(s)): imgs.add(i[1])
    print('IMGS:',*sorted(imgs),sep='\n ')
