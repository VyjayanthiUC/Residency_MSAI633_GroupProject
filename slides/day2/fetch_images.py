#!/usr/bin/env python3
"""Download the few game images the deck shows into img/ (git-ignored).

The images are HoYoverse game art that the Genshin Impact Fandom wiki shows under fair use; they are NOT committed to
this repository. The URLs are the same ones the team website picks from the snapshot's raw crawl (web/images.py).

    python3 slides/day2/fetch_images.py
"""
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "https://static.wikia.nocookie.net/gensin-impact/images/"
UA = "msai633-genshin-rag/0.1 (University of the Cumberlands coursework)"
IMAGES = {  # local name: (path on the wiki's image server, width)
    "lauma.webp": ("2/27/Lauma_Icon.png", 320),
    "ineffa.webp": ("0/0b/Ineffa_Icon.png", 320),
    "flins.webp": ("a/af/Flins_Icon.png", 320),
    "columbina.webp": ("3/35/Columbina_Icon.png", 320),
    "nightweaver.webp": ("a/a7/Weapon_Nightweaver%27s_Looking_Glass.png", 320),
    "v71.webp": ("9/98/Splashscreen_A_Rekviem_for_the_Underworld.png", 1920),
}

out = HERE / "img"
out.mkdir(exist_ok=True)
for name, (path, width) in IMAGES.items():
    dest = out / name
    if dest.exists():
        continue
    url = f"{BASE}{path}/revision/latest/scale-to-width-down/{width}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
        dest.write_bytes(r.read())
    print(f"saved img/{name}")
    time.sleep(1)  # same politeness as the crawl: at most one request per second
print("images ready")
