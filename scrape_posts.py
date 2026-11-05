#!/usr/bin/env python3
"""Convertit les articles WordPress/Elementor en blocs propres (JSON)."""
import bs4, glob, json, os, re, sys
from urllib.parse import urlparse

ALLOWED = {"p", "ul", "ol", "li", "strong", "em", "b", "i", "a", "br", "h2", "h3", "h4", "blockquote"}


def best_src(img):
    cands = []
    for attr in ("data-srcset", "srcset"):
        ss = img.get(attr)
        if ss:
            for part in ss.split(","):
                bits = part.strip().split()
                if len(bits) == 2 and bits[1].endswith("w"):
                    cands.append((int(bits[1][:-1]), bits[0]))
    good = [c for c in cands if c[0] <= 1400]
    if good:
        return max(good)[1]
    src = img.get("data-src") or img.get("data-lazy-src") or img.get("src") or ""
    if src.startswith("data:"):
        return ""
    return src


def clean_html(node):
    node = bs4.BeautifulSoup(str(node), "html.parser")
    for t in node(["script", "style", "noscript", "svg", "img", "figure", "iframe"]):
        t.decompose()
    for t in node.find_all(True):
        if t.name in ("h1", "h5", "h6"):
            t.name = "h3"
        if t.name == "b":
            t.name = "strong"
        if t.name == "i":
            t.name = "em"
        if t.name not in ALLOWED:
            t.unwrap()
            continue
        href = t.get("href") if t.name == "a" else None
        t.attrs = {}
        if href:
            t["href"] = href
    out = str(node)
    out = re.sub(r"&nbsp;| ", " ", out)
    out = re.sub(r"\s+", " ", out).strip()
    out = re.sub(r"<p>\s*</p>", "", out)
    if out and not out.startswith("<"):
        out = f"<p>{out}</p>"
    return out


def convert(path):
    s = bs4.BeautifulSoup(open(path, encoding="utf-8"), "html.parser")
    slug = os.path.basename(path)[:-5]
    root = s.select("[data-elementor-type=wp-post]")[0]
    og = s.find("meta", property="og:image")
    date = s.find("meta", property="article:published_time")
    desc = s.find("meta", attrs={"name": "description"}) or s.find("meta", property="og:description")
    title_tag = s.find("meta", property="og:title")
    blocks, title, images = [], None, []
    import html as _h
    page_title = re.split(r"\s+-\s+Lovely Day Event", _h.unescape(title_tag["content"]))[0].strip() if title_tag else slug
    title = page_title
    for w in root.select("[data-widget_type]"):
        wt = w["data-widget_type"].split(".")[0]
        if w.find_parent(attrs={"data-widget_type": True}):
            continue
        if wt == "heading":
            h = w.find(re.compile("^h[1-6]$|^p$|^span$|^div$"), class_=re.compile("elementor-heading-title"))
            if not h:
                continue
            txt = re.sub(r"\s+", " ", h.get_text(" ", strip=True))
            if not txt:
                continue
            if h.name == "h1" and txt == page_title:
                continue
            lvl = {"h2": "h2", "h3": "h3", "h1": "h2"}.get(h.name, "h3")
            blocks.append({"t": lvl, "v": txt})
        elif wt == "text-editor":
            html = clean_html(w.select_one(".elementor-widget-container") or w)
            if html:
                blocks.append({"t": "html", "v": html})
        elif wt in ("image", "image-box"):
            img = w.find("img")
            if img:
                u = best_src(img)
                if u and "logo" not in u.lower() and "removebg" not in u.lower():
                    blocks.append({"t": "img", "v": u, "alt": img.get("alt", "")})
                    images.append(u)
            if wt == "image-box":
                ttl = w.select_one(".elementor-image-box-title")
                dsc = w.select_one(".elementor-image-box-description")
                if ttl and ttl.get_text(strip=True):
                    blocks.append({"t": "h3", "v": ttl.get_text(" ", strip=True)})
                if dsc and dsc.get_text(strip=True):
                    blocks.append({"t": "html", "v": clean_html(dsc)})
        elif wt == "icon-box":
            ttl = w.select_one(".elementor-icon-box-title")
            dsc = w.select_one(".elementor-icon-box-description")
            if ttl and ttl.get_text(strip=True):
                blocks.append({"t": "h3", "v": ttl.get_text(" ", strip=True)})
            if dsc and dsc.get_text(strip=True):
                blocks.append({"t": "html", "v": clean_html(dsc)})
        elif wt in ("uael-image-gallery", "image-gallery", "image-carousel"):
            urls = []
            for img in w.find_all("img"):
                u = best_src(img)
                if u and u not in urls:
                    urls.append(u)
            for a in w.find_all("a", href=True):
                if re.search(r"\.(jpe?g|png|webp)$", a["href"], re.I) and not urls:
                    urls.append(a["href"])
            if urls:
                blocks.append({"t": "gallery", "v": urls})
                images += urls
        elif wt == "testimonial":
            c = w.select_one(".elementor-testimonial-content")
            n = w.select_one(".elementor-testimonial-name")
            if c and c.get_text(strip=True):
                blocks.append({"t": "quote", "v": re.sub(r"\s+", " ", c.get_text(" ", strip=True)), "who": n.get_text(" ", strip=True) if n else ""})
        elif wt == "icon-list":
            items = [re.sub(r"\s+", " ", li.get_text(" ", strip=True)) for li in w.select("li")]
            items = [i for i in items if i]
            if items:
                blocks.append({"t": "html", "v": "<ul>" + "".join(f"<li>{bs4.BeautifulSoup(i,'html.parser').get_text()}</li>" for i in items) + "</ul>"})
        elif wt == "video":
            # lien vers la vidéo plutôt qu'un iframe
            import html as H
            settings = w.get("data-settings", "")
            m = re.search(r'https?:\\?/\\?/[^"]+', settings)
            if m:
                blocks.append({"t": "html", "v": f'<p><a href="{m.group(0).replace(chr(92), "")}">Voir la vidéo</a></p>'})
    # fusion des blocs html contigus
    merged = []
    for b in blocks:
        if merged and b["t"] == "html" and merged[-1]["t"] == "html":
            merged[-1]["v"] += b["v"]
        else:
            merged.append(b)
    if not title:
        title = (title_tag["content"] if title_tag else slug).split(" - ")[0].strip()
    return {
        "slug": slug,
        "title": title,
        "date": date["content"][:10] if date else "",
        "cover": og["content"] if og else (images[0] if images else ""),
        "desc": desc["content"] if desc else "",
        "blocks": merged,
    }


if __name__ == "__main__":
    out = [convert(f) for f in sorted(glob.glob("posts/*.html"))]
    json.dump(out, open("posts.json", "w"), ensure_ascii=False, indent=1)
    imgs = set()
    for p in out:
        if p["cover"]:
            imgs.add(p["cover"])
        for b in p["blocks"]:
            if b["t"] == "img":
                imgs.add(b["v"])
            if b["t"] == "gallery":
                imgs.update(b["v"])
    print(len(out), "articles", len(imgs), "images uniques")
    open("post_images.txt", "w").write("\n".join(sorted(imgs)))
