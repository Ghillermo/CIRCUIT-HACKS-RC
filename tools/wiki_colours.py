"""The wiki's patch colour chart (the user, 2026-11-13: «Add the color chart to the wiki and provide link»): docs/wiki/Patch-Colours.md and
Patch-Colours-ES.md with an SVG chart in docs/wiki/img/ (nova-colours-en.svg / -es.svg).  The colours are read from tools/sd_app.html (NOVA_CATS,
NOVA_CAT_RGB, TRACK_RGB: the LED table's RGB of packio.CAT_PAL, Beta 5.40 on), so the chart, the SD app's colour key and the device agree.

    python tools/wiki_colours.py
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = "https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/"
PAGES = "https://ghillermo.github.io/CIRCUIT-HACKS-RC/"
NAME_EN = ["None", "Arp", "Bass", "Bell", "Classic", "Drum", "Keyboard", "Lead", "Movement", "Pad", "Poly", "SFX", "String", "User", "Voc"]
COL_EN = ["the track's colour", "teal", "steel blue", "light blue", "amber", "orange", "pale lime", "yellow", "violet", "blue", "green", "red", "peach",
          "sand", "lavender"]
COL_ES = ["el color de la pista", "verde azulado", "azul acero", "azul claro", "ámbar", "naranja", "lima claro", "amarillo", "violeta", "azul", "verde",
          "rojo", "melocotón", "arena", "lavanda"]


def app_colours():
    s = (ROOT / "tools/sd_app.html").read_text(encoding="utf-8")
    cats = json.loads(re.search(r"const NOVA_CATS = (\[[\s\S]*?\]\]);", s).group(1))
    rgb = json.loads(re.search(r"const NOVA_CAT_RGB = (\[[^\]]*\]);", s).group(1))
    trk = json.loads(re.search(r"const TRACK_RGB = (\[[^\]]*\]);", s).group(1))
    assert [c[1] for c in cats] == NAME_EN and len(rgb) == 15 and rgb[0] is None
    return cats, rgb, trk


def svg(lang, cats, rgb, trk):
    rows, w, h, cw = 5, 660, 0, 220
    n = len(cats); per = (n + 2) // 3
    h = 54 + per * 40 + 12
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{"Nova patch categories and their colours" if lang == "en" else "Categorías de los patches Nova y sus colores"}">',
           f'<rect x="0" y="0" width="{w}" height="{h}" rx="14" fill="#17181b"/>',
           f'<text x="20" y="32" font-size="15" font-weight="600" fill="#e6e8eb" font-family="sans-serif">{"Synth 1 / 2 Preset view: patch colour by Components category" if lang == "en" else "Vista Preset de Synth 1 / 2: color del patch por categoría de Components"}</text>']
    for i, (es, en) in enumerate(cats):
        col, row = i // per, i % per
        x, y = 20 + col * cw, 54 + row * 40
        if i == 0:
            out.append(f'<rect x="{x}" y="{y}" width="28" height="28" rx="6" fill="{trk[0]}"/>')
            out.append(f'<polygon points="{x + 28},{y} {x + 28},{y + 28} {x},{y + 28}" fill="{trk[1]}"/>')
        else:
            out.append(f'<rect x="{x}" y="{y}" width="28" height="28" rx="6" fill="{rgb[i]}"/>')
        name = en if lang == "en" else es
        sub = (COL_EN if lang == "en" else COL_ES)[i]
        out.append(f'<text x="{x + 38}" y="{y + 13}" font-size="13" fill="#e6e8eb" font-family="sans-serif">{name}</text>')
        out.append(f'<text x="{x + 38}" y="{y + 27}" font-size="11" fill="#9aa1a9" font-family="sans-serif">{sub}{"" if i == 0 else " · " + rgb[i]}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def page(lang, cats, rgb, trk):
    en = lang == "en"
    me, other = ("Patch-Colours", "Patch-Colours-ES") if en else ("Patch-Colours-ES", "Patch-Colours")
    L = [f"# {'Patch colours' if en else 'Colores de los patches'}", "",
         f"*[{'Versión en español' if en else 'English version'}]({WIKI}{other}) · [Home]({WIKI}{'Home' if en else 'Home#en-español'}) · "
         f"[{'Guide by views' if en else 'Guía por vistas'}]({PAGES}beta/{'guide' if en else 'guia'}.html#synth-preset)*", ""]
    if en:
        L += ["In the **Synth 1 / 2 Preset view** each Nova patch lights in the colour of its **Components category** (Beta 5.40 and later). "
              "Category None keeps the track's colour (Synth 1 magenta, Synth 2 green); an empty slot is dim white and the chosen patch is white. "
              "The release candidates (RC4.10 on) use the original's colours: every patch in the track's colour.", ""]
    else:
        L += ["En la **vista Preset de Synth 1 / 2** cada patch Nova se enciende en el color de su **categoría de Components** (Beta 5.40 y posteriores). "
              "La categoría Ninguna lleva el color de la pista (Synth 1 magenta, Synth 2 verde); un hueco vacío, blanco tenue, y el patch elegido, blanco. "
              "Las versiones candidatas (desde RC4.10) usan los colores del original: todos los patches en el color de la pista.", ""]
    L += [f'<img src="img/nova-colours-{lang}.svg" width="660" alt="{"Nova patch categories and their colours" if en else "Categorías de los patches Nova y sus colores"}">', ""]
    L += [f"| # | {'Category' if en else 'Categoría'} | {'Colour' if en else 'Color'} | RGB |", "|---|---|---|---|"]
    for i, (es, name) in enumerate(cats):
        hexs = f"{trk[0]} / {trk[1]}" if i == 0 else rgb[i]
        L.append(f"| {i} | {name if en else es} | {(COL_EN if en else COL_ES)[i]} | `{hexs}` |")
    L += [""]
    if en:
        L += ["## Setting a patch's category", "",
              "- **On the device:** save the patch in the Synth 1 / 2 Preset view (**Clear + pad**, then **Clear + the same pad** to confirm); while it asks, **K1** picks the category.",
              "- **In Novation Components:** the category of each patch of the pack.",
              f"- **In the SD app** ([download]({PAGES}sd_app.zip)): the **Nova synths** tab shows each patch's colour and, on top, this chart as a colour key.", ""]
    else:
        L += ["## Elegir la categoría de un patch", "",
              "- **En el aparato:** guarda el patch en la vista Preset de Synth 1 / 2 (**Clear + pad**, luego **Clear + el mismo pad** para confirmar); mientras pregunta, **K1** elige la categoría.",
              "- **En Novation Components:** la categoría de cada patch del pack.",
              f"- **En la app de la tarjeta** ([descarga]({PAGES}sd_app.zip)): la pestaña **Sintes Nova** enseña el color de cada patch y, arriba, esta tabla como clave de colores.", ""]
    return "\n".join(L)


def main():
    cats, rgb, trk = app_colours()
    for lang in ("en", "es"):
        (ROOT / f"docs/wiki/img/nova-colours-{lang}.svg").write_text(svg(lang, cats, rgb, trk), encoding="utf-8")
        name = "Patch-Colours" if lang == "en" else "Patch-Colours-ES"
        (ROOT / f"docs/wiki/{name}.md").write_text(page(lang, cats, rgb, trk), encoding="utf-8")
    print("Patch-Colours(-ES).md, img/nova-colours-en/es.svg")


if __name__ == "__main__":
    main()
