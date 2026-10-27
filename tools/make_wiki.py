"""The wiki pages made from the manual (the user, 2026-10-27: «Make new sections: Views, Data, Features, DSP, Usability, MIDI; keep everything user
level, don't discuss reverse engineering or inner tests»): docs/wiki/{Views,Data,Features,DSP,Usability,MIDI}.md and their -ES twins, from the guide
by views (make_guide / guide_en), the feature list (make_manual) and the MIDI reference (midi_ref, through the guide's MIDI view).  Home, FAQ and
Roadmap are written by hand.  Copy docs/wiki/*.md into the wiki repository (CIRCUIT-HACKS-RC.wiki.git) to publish.

    python tools/make_wiki.py
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_guide as G  # noqa: E402
import make_manual as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PAGES = "https://ghillermo.github.io/CIRCUIT-HACKS-RC/"
WIKI = "https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/"
GUIDE = dict(en=PAGES + "guide.html", es=PAGES + "guia.html")
# words that belong to the inner works, never in a wiki page (checked on every page)
BANNED = re.compile(r"\b(0x[0-9A-Fa-f]+|DSP56|RAM|SPI|ARM|emulat\w*|emulac\w*|revers\w* engineer\w*|ingenier\w* inversa|hook\w*|gancho\w*|"
                    r"firmware's (own )?table|tabla del (propio )?firmware|bytes?|núcleo|cores?|XMEM|registers?|builders?|test suite)\b", re.I)

T = dict(
    en=dict(other="Versión en español", home="Home", guide="Guide by views", full="Full details in the guide", how="How to get there:", about="In this view",
            views=("Views", "Every view of the device and what it offers. Each one links to its full chapter in the [guide by views]({g})."),
            data=("Data", "What is saved where, how to make sure it is saved, and what is lost when you switch off."),
            feat=("Features", "Every feature in one line, by topic. Each one links to its illustrated entry; the [guide by views]({g}) explains them view by view."),
            dsp=("DSP", "The sound side of the mod: the synth engines of the MIDI tracks, the new drum controls and the effects.",
                 """The **MIDI 1 / 2** tracks get their own synth inside the device, with several engines on the engine row of their Preset view: an
**oscillator** that morphs between sine, triangle, saw (up to a seven-saw **supersaw**) and pulse, with wavefolding; **two oscillators** with FM, sync,
ring and mix; a **VA-drum** for percussive sounds; a **granular** engine that plays grains of a sample or of the live capture; a **4-operator FM**
engine with 16 algorithms; and a **sample mode** that plays the pack's samples across the keyboard, in stereo if you like. It has a filter with
several types, envelopes, an LFO with seven shapes (synced to the tempo if you want), a **mod matrix**, **polyphony** with eight voice modes, and
eight automation lanes. The **drums** gain envelopes, a ring modulator, an LFO, filter modes, sample start and end, attack, bitcrush and distortion
types. **Master FX** adds performance effects to the whole mix, and the **FX** and **Sidechain** views expose the reverb, delay, side-chain and
master compressor settings."""),
            usab=("Usability", "The conventions that make the mod predictable, the shortcuts that work in every view, and the playing and recording helpers.",
                  "Playing and recording"),
            midi=("MIDI", "How the mod talks MIDI: its own behaviours, the new CCs and NRPNs, and the mod matrix and macro destinations.")),
    es=dict(other="English version", home="Inicio", guide="Guía por vistas", full="Todo el detalle en la guía", how="Cómo se llega:", about="En esta vista",
            views=("Vistas", "Cada vista del aparato y lo que ofrece. Cada una enlaza con su capítulo completo de la [guía por vistas]({g})."),
            data=("Datos", "Qué se guarda y dónde, cómo asegurarte de que se guarda y qué se pierde al apagar."),
            feat=("Funciones", "Cada función en una línea, por temas. Cada una enlaza con su entrada ilustrada; la [guía por vistas]({g}) las explica vista por vista."),
            dsp=("DSP", "La parte de sonido del mod: los motores del sinte de las pistas MIDI, los controles nuevos de los drums y los efectos.",
                 """Las pistas **MIDI 1 / 2** tienen un sinte propio dentro del aparato, con varios motores en la fila de motores de su vista Preset: un
**oscilador** que pasa del seno al triángulo, la sierra (hasta una **supersaw** de siete sierras) y el pulso, con wavefold; **dos osciladores** con FM,
sync, ring y mezcla; un **VA-drum** para sonidos percusivos; un motor **granular** que toca granos de un sample o de la captura en directo; un motor
**FM de 4 operadores** con 16 algoritmos; y un **modo muestra** que toca los samples del pack a lo largo del teclado, en estéreo si quieres. Tiene un
filtro de varios tipos, envolventes, un LFO con siete formas (a tempo si quieres), una **matriz de modulación**, **polifonía** con ocho modos de voz y
ocho carriles de automatización. Los **drums** ganan envolventes, ring mod, LFO, modos de filtro, inicio y final del sample, ataque, bitcrush y tipos
de distorsión. **Master FX** añade efectos de directo a toda la mezcla, y las vistas **FX** y **Sidechain** dan acceso a la reverb, el delay, el
sidechain y el compresor master."""),
            usab=("Usabilidad", "Las convenciones que hacen el mod previsible, los atajos que valen en todas las vistas y las ayudas para tocar y grabar.",
                  "Tocar y grabar"),
            midi=("MIDI", "Cómo habla MIDI el mod: sus comportamientos propios, los CC y NRPN nuevos, y la matriz de modulación y los destinos de los macros.")))
PAGE = dict(views="Views", data="Data", feat="Features", dsp="DSP", usab="Usability", midi="MIDI")
DSP_VIEWS = ("midi-preset", "midi-knobs", "midi-fm", "midi-muestra", "midi-matriz", "synth-fuente", "drum-pista", "drum-cromatica", "master-fx", "vista-fx", "sidechain")
USAB_VIEWS = ("synth-nota", "escalas", "micropasos", "pattern-settings")
DEV = {"herramientas"}                # the feature list's developer tools: not for the wiki


def name(key, lang): return PAGE[key] + ("-ES" if lang == "es" else "")


def absolute(text, lang):
    """the guide's own links (#view) -> the guide's page"""
    return re.sub(r"\]\(#([\w-]+)\)", lambda m: f"]({GUIDE[lang]}#{m.group(1)})", text)


def head(key, lang):
    t = T[lang]; title, intro = t[key][0], t[key][1].format(g=GUIDE[lang])
    other = name(key, "en" if lang == "es" else "es")
    return [f"# {title}", "", f"*[{t['other']}]({WIKI}{other}) · [{t['home']}]({WIKI}{'Home' if lang == 'en' else 'Home#en-español'}) · "
            f"[{t['guide']}]({GUIDE[lang]})*", "", intro, ""]


def summary(v, lang, level="###"):
    t = T[lang]
    out = [f"{level} {v['title']}", "", f"*{t['how']}* {v['how']}", ""]
    if v["about"]: out += [v["about"], ""]
    out += [f"→ [{t['full']}]({GUIDE[lang]}#{v['id']})", ""]
    return out


RENAME = {"convenciones": dict(en="Conventions", es="Convenciones")}


def full(v, lang, level="##"):
    title = RENAME.get(v["id"], {}).get(lang, v["title"])
    how = v["how"] if v["part"] in ("0", "11") else f"*{T[lang]['how']}* {v['how']}"        # the data / MIDI chapters' first line is not a way in
    return [f"{level} {title}", "", how, "", v["detail"].replace("\n### ", f"\n{level}# "), ""]


def pages(lang):
    views, parts, _ = G.data(lang)
    by = {v["id"]: v for v in views}
    out = {}
    # Views: parts 1-10 (setup to packs), the summaries
    L = head("views", lang)
    for p, pname in parts:
        if p in ("0", "11", "A"): continue
        L += [f"## {pname}", ""]
        for v in views:
            if v["part"] == p: L += summary(v, lang)
    out["views"] = L
    # Data: the data chapter's first three views in full
    L = head("data", lang)
    for vid in ("datos-patron", "guardado", "datos-perdido"): L += full(by[vid], lang)
    out["data"] = L
    # Features: the feature list
    M.use(lang)
    L = head("feat", lang)
    for g, gname in M.CUR["GROUPS"]:
        L += [f"## {gname}", ""]
        L += [f'- **[{s_["title"]}]({M.PAGES_URL[lang]}#{M.anchor(code, s_)})** — ' + " ".join(s_["summary"])
              for code, s_ in M.numbered() if s_["group"] == g and s_["id"] not in DEV]
        L.append("")
    out["feat"] = L
    # DSP: the overview, then the sound views' summaries (in full when the view has no summary)
    L = head("dsp", lang) + [T[lang]["dsp"][2], ""]
    for vid in DSP_VIEWS:
        v = by[vid]
        L += summary(v, lang, "##") if v["about"] else full(v, lang)
    out["dsp"] = L
    # Usability: the conventions, the buttons of every view, then the playing / recording views' summaries
    L = head("usab", lang)
    for vid in ("convenciones", "botones"): L += full(by[vid], lang)
    L += [f"## {T[lang]['usab'][2]}", ""]
    for vid in USAB_VIEWS: L += summary(by[vid], lang)
    out["usab"] = L
    # MIDI: the MIDI view (with the reference's tables) and the mod matrix / macro destinations view
    L = head("midi", lang)
    for vid in ("midi", "destinos"): L += full(by[vid], lang)
    out["midi"] = L
    return out


def main():
    bad = []
    for lang in ("en", "es"):
        for key, lines in pages(lang).items():
            text = absolute("\n".join(lines), lang)
            text = G.marks(text, G.B, G.NB, G.XB) if lang == "es" else text
            while "\n\n\n" in text: text = text.replace("\n\n\n", "\n\n")
            for m in BANNED.finditer(text): bad.append((name(key, lang), text[max(0, m.start() - 60):m.end() + 40].replace("\n", " ")))
            (ROOT / "docs/wiki" / f"{name(key, lang)}.md").write_text(text.rstrip() + "\n", encoding="utf-8", newline="")
    sys.stdout.reconfigure(encoding="utf-8")
    for p, ctx in bad: print(f"inner works? {p}: …{ctx}…")
    print("12 pages,", len(bad), "flags")
    return len(bad)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
