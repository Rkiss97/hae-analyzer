"""
HAE Elemző - Törvény Indokolás Hozzáadott Érték Vizsgálat
Streamlit alkalmazás Claude Opus 4.5 API-val
"""

import streamlit as st
import anthropic
import re
from dataclasses import dataclass
from typing import List, Dict

# ============================================================
# KATEGÓRIÁK ÉS SZÍNEK
# ============================================================

HAE_CATEGORIES = {
    1: ("CÉLMEGHATÁROZÁS", "#E53935"),
    2: ("BELSŐ UTALÁS", "#9E9E9E"),
    3: ("KÜLSŐ JOGFORRÁS HIVATKOZÁS", "#03A9F4"),
    4: ("BÍRÓSÁGI JOGGYAKORLAT ÉS AB HATÁROZATOK", "#2E7D32"),
    5: ("SZAKIRODALOM / KUTATÁSI EREDMÉNY", "#795548"),
    6: ("ÖSSZEVETÉS KORÁBBI SZABÁLYOZÁSSAL", "#4CAF50"),
    7: ("HATÁSVIZSGÁLAT", "#FF9800"),
    8: ("EGYÉB MAGYARÁZAT ÉS PÉLDÁK", "#FFEB3B"),
}

NEM_CATEGORIES = {
    1: ("SZÓ SZERINTI ÁTMÁSOLÁS", "#9C27B0"),
    2: ("ÁTFOGALMAZÁS", "#1565C0"),
    3: ("KIVONATOLÁS", "#E0E0E0"),
    4: ("HIBÁS INDOKOLÁS", "#212121"),
}

# ============================================================
# SYSTEM PROMPT - EREDETI
# ============================================================

SYSTEM_PROMPT = """

───────────────────────────────────────────────────────────────────────
ALAPKÉRDÉS
───────────────────────────────────────────────────────────────────────

Minden szövegrésznél döntsd el: magyaráz-e az indokolás, vagy csak
megismétli a törvényszöveget más szavakkal?

Magyarázat: segíti a megértést, kontextust ad, indokol, értékel,
vagy olyan információt közöl, ami a törvényszövegből nem olvasható ki.

Nem magyarázat: ha más szavakkal mondja ugyanazt, amit a törvény,
vagy összefoglalja annak tartalmát.

───────────────────────────────────────────────────────────────────────
HOZZÁADOTT ÉRTÉK KATEGÓRIÁK - jelölés: [HAE:n]...[/HAE]
───────────────────────────────────────────────────────────────────────

[HAE:1] Célmeghatározás
   A TÖRVÉNY vagy a KONKRÉT SZAKASZ céljának, a JOGALKOTÓ SZÁNDÉKÁNAK,
   a SZABÁLYOZÁS CÉLJÁNAK EXPLICIT megfogalmazása.

   Jellemző fordulatok:
   - "a törvény célja, hogy"
   - "e szakasz célja"
   - "a szabályozás célja"
   - "e rendelkezés célja"
   - "a jogalkotó szándéka"
   - "célul tűzi ki"

   NEM ide tartozik (ezek HAE:8 – egyéb magyarázat):
   - "X érdekében Y-t tesz lehetővé" - ez magyarázat, de nem célmeghatározás
   - "a közbiztonság érdekében" - ez magyarázat, de nem feltétlenül a törvény célja
   - "a feladatok ellátása érdekében" - ez kontextus, további magyarázat, ha nem szerepel a törvényben
   - "lehetőséget ad arra, hogy" - ez amit a törvény tesz, de nem cél
   - "megteremti a lehetőségét annak, hogy" - ez eredmény, de nem cél
   - "szükségessé válhat" - ez magyarázat, de nem célmeghatározás
   - "elengedhetetlen" - ez magyarázat, de nem célmeghatározás

   A cél a MIÉRT, nem a MIT. Ha az indokolás azt írja le zanzásítva, hogy mit tesz lehetővé a törvény, az kivonatolás (NEM:3) vagy átfogalmazás (NEM:2), nem célmeghatározás.

   Példa - HAE:1 (valódi célmeghatározás):
   "A törvény célja a gyülekezési jog gyakorlásának szabályozása."
   "A jogalkotó szándéka a korábbi hiányosságok orvoslása."

   Példa - HAE:8 (magyarázat, NEM célmeghatározás):
   "A közbiztonság érdekében szükségessé válhat az ellenőrzés."
   "A feladatok ellátása érdekében elengedhetetlen a jelenlét."
   "Ez az együttműködési kötelezettség garantálja a békés jelleg biztosítását."
   (Ez utóbbi azért HAE:8, mert:
   Leírja az eredményt (mit garantál)
   Magyarázza a szabály funkcióját
   De NEM mondja ki, hogy "a törvény célja" vagy "a jogalkotó szándéka", adott jogintézmény, szakasz, bevezetett jogintézmény stb. célja mi lenne)

[HAE:2] Belső utalás (ugyanezen törvényen belüli kereszthivatkozás)
   Utalás a fenti törvényszöveg más rendelkezéseire.
   Példák: "az 51. § szerinti szabályokat alkalmazni kell",
   "a fenti szabályokkal összhangban", "e törvény 10. §-a alapján", "a javaslat 2. § (2) bekezdése egyértelművé teszi"

[HAE:3] Külső jogforrás hivatkozás (más jogszabályra utalás)
   Konkrétan megnevezett más jogszabályra való hivatkozás (akár konkrét jogszabály szám nélkül).
   Példák: "az Alaptörvény 15. cikk (2) bekezdése szerint",
   "a 2010. évi XLIII. törvény (Ksztv.) szabályozását átvéve",
   "a Ksztv. rendelkezéseit átemelve", "a Ptk. szerint"
   "a jogalkotásról szóló törvény alapján", "a kereskedelemről szóló törvényben meghatározott"
   Ide tartoznak az alacsonyabb jogforrásokra (kormányrendeletekre) való utalások is.
   Példák: "a veszélyhelyzet kihirdetéséről szóló 478/2020. (XI. 3.) Korm. rendelet szerinti"

   Fontos, hogy salátatörvény jellegű (sok törvényt egyszerre módosító) törvényeknél pusztán azért, mert a szövegben van más jogszabály neve, nem HAE, ha pont azt a jogszabályt módosítja.

[HAE:4] Bírósági joggyakorlat és AB határozatok
   Bírósági döntésekre, AB határozatokra, EJEB döntésére, joggyakorlatra, bírósági gyakorlatra, konkrét ítéletre való utalás.
   Példák: "a bírói gyakorlattal egyezően", "az AB határozat alapján", "általános joggyakorlattal egyezően"
   Ide tartozik: joggyakorlat alapján levont olyan következtetés, ami közvetlen utalást tartalmaz valamilyen bírósági álláspontra, jogalkalmazói visszajelzés alapján történő jogalkotásra való utalás, bíróságok álláspontjának kifejtése, arra való konkrét utalással
   Nem tartozik ide: alapvető jogokra való általános utalás

[HAE:5] Szakirodalom, kutatási eredmény
   Tudományos művekre, szakmai jelentésekre való hivatkozás.
   Példák: "a KSH jelentése szerint", "az OECD ajánlásaival összhangban", "Vékás Lajos professzor munkái", "a szakirodalom álláspontját követve", "a szakirodalmi álláspont alapján"

[HAE:6] Összevetés korábbi szabályozással
   A korábbi és új szabályozás viszonyának bemutatása, konkrét
   jogszabály megnevezése nélkül.
   Példák: "a korábbi szabályozással egyezően", "a hatályos
   szabályozást átvéve", "új eleme a törvénynek", "korábban nem volt", "közjogi hagyományoknak megfelelően", "fontos változás", "vonatkozó rendelkezések elhagyásra kerültek", "továbbra is", "adott rendelkezés kivezetésével"
   Ide tartozik, ha az indokolás jelzi, hogy valami "új", "bevezet", "meghonosít", "kivezet", "megszüntet", "rendelkezést fenntart", "változtat", "eltörli" - ez korábbi állapothoz való viszonyítás.

[HAE:7] Hatásvizsgálat
   A szabályozás hatásainak bemutatása KONKRÉT ADATOKKAL, SZÁMOKKAL
   alátámasztva. Előzetes hatásvizsgálatra, kutatásra, felmérésre való
   hivatkozás eredményekkel.

   Ide tartozik, ha az indokolás tartalmaz:
   - Érintett csoportok létszámát (fő, db, vállalkozás)
     Pl. "kb. 50 000 vállalkozást érint", "1 millió nyugdíjast érint"
   - Költségvetési / gazdasági hatást konkrét összeggel (Ft)
     Pl. "évi 2 milliárd Ft megtakarítás", "500 millió Ft többletkiadás"
   - Adminisztratív terhek változását számszerűsítve (Ft, óra, %)
     Pl. "évi 10 000 Ft/vállalkozás tehercsökkenés", "30%-kal kevesebb ügyintézési idő"
   - Foglalkoztatási hatást létszámmal
     Pl. "200 új munkahely", "50 fős létszámcsökkenés"
   - Más országok tapasztalatát konkrét eredményekkel
     Pl. "Ausztriában 15%-os növekedést eredményezett, a hatásvizsgálat alapján hasonló hatások várhatók Magyarországon is a szabályozás bevezetésével"
   - Konkrét időtávot
     Pl. "2020-2024 között", "a bevezetést követő 4 évben"

   NEM ide tartozik (ezek HAE:8):
   - "adminisztratív terheket csökkent" (szám nélkül)
   - "a jogalkalmazást megkönnyíti" (konkrétum nélkül)
   - "költségvetési hatása minimális" (összeg nélkül)
   - "a többi EU tagállamhoz hasonlóan" (eredmény nélkül)
   - "gazdasági szempontból indokolt" (adat nélkül)
   - "széles társadalmi réteget érint" (létszám nélkül)

[HAE:8] Egyéb magyarázat és példák
   Indokolás, érvelés, háttérinformáció, összefüggés-feltárás.
   Példák: "tekintettel arra, hogy", "figyelemmel arra", "mivel",
   "ezért szükséges", "ugyanis", "ennek indoka"
   Ide tartoznak a törvényben nem szereplő konkrét példák is.

   Ide tartozik még:
   - Általános hatásokra utalás konkrét adat nélkül
     ("csökkenti a terheket", "megkönnyíti a jogalkalmazást")
   - Nemzetközi összehasonlítás adatok nélkül
     ("EU tagállamokhoz hasonlóan", "nemzetközi gyakorlatnak megfelelően")

───────────────────────────────────────────────────────────────────────
NEM HOZZÁADOTT ÉRTÉK KATEGÓRIÁK - jelölés: [NEM:n]...[/NEM]
───────────────────────────────────────────────────────────────────────

[NEM:1] Szó szerinti átmásolás
   A törvényszöveg változtatás nélküli átvétele.

[NEM:2] Átfogalmazás (parafrázis)
   A törvényszöveg más szórenddel, szinonimákkal való visszaadása,
   amely nem ad új információt.

[NEM:3] Kivonatolás
   A törvényszöveg tömörítése, összefoglalása magyarázat nélkül.
   Jellemző formulák: "a törvény rendelkezik", "meghatározza",
   "szabályozza", "rögzíti", "kimondja"
   Szintén ide tartozik, ha az indokolás csak annyit mond, de nem fejti ki jobban a mögöttes okokat vagy egyéb részleteket, hogy "hatályon kívül helyező rendelkezések", "jogtechnikai jellegű pontosítás", " felhatalmazó rendelkezések",
   "technikai jellegű szövegcserés módosítás", "terminológiai pontosítást tartalmaz", "jogharmonizációs záradékot tartalmaz", "nyelvhelyességi korrekció", "hatályon kívül helyező rendelkezéseket tartalmaz", "sarkalatossági záradék kiegészítése", "átmeneti rendelkezés" - és ehhez hasonló tartalomjegyzék szerű kivonatolások

[NEM:4] Hibás indokolás
   Ide tartozik:
   - Ellentmondás: az indokolás tartalmilag ellentmond a törvényszövegnek
   - Normaszöveghez nem kapcsolódó magyarázat: az indokolás nem a hivatkozott szakaszhoz
     kapcsolódik, hanem más rendelkezéseket ismertet, tartalmilag nincsen köze a hozzá tartozó törvényszöveghez.
     Olyan többlet információk, amik nem amgyarázatok, hanem túllépnek a normaszövegen, az abban található állításokból egyáltalán nem következnek.


───────────────────────────────────────────────────────────────────────
SZEGMENTÁLÁSI SZABÁLYOK
───────────────────────────────────────────────────────────────────────

Kötelező mondaton belül is szegmentálni, ha vegyes a tartalom.
Ezekben az esetekben ne annotálj teljes mondatokat egyben!

Példa - beékelt HAE:6:
"A törvény - a hatályos szabályozást átvéve - rendelkezik a testületekről."

Helyes annotáció:
[NEM:3]A törvény -[/NEM] [HAE:6]a hatályos szabályozást átvéve[/HAE] [NEM:3]- rendelkezik a testületekről.[/NEM]

Példa - beékelt HAE:3:
"A törvény - átemelve a Ksztv. rendelkezéseit - meghatározza a hatásköröket."

Helyes annotáció:
[NEM:3]A törvény -[/NEM] [HAE:3]átemelve a Ksztv. rendelkezéseit[/HAE] [NEM:3]- meghatározza a hatásköröket.[/NEM]

Példa - célmeghatározás + kivonatolás:
"A törvény a szervi és személyi megközelítés egységét tűzi ki célul, szabályozza a szervek jogállását."

Helyes annotáció:
[HAE:1]A törvény a szervi és személyi megközelítés egységét tűzi ki célul,[/HAE] [NEM:3]szabályozza a szervek jogállását.[/NEM]

Figyelj a gondolatjelek, zárójelek közötti beszúrásokra - ezek gyakran
külön kategóriába tartoznak!

───────────────────────────────────────────────────────────────────────
ELHATÁROLÁSOK
───────────────────────────────────────────────────────────────────────

HAE:2 vs HAE:3 vs HAE:6:
- Ugyanezen törvény szakaszára utal → HAE:2
- Más jogszabályra, konkrétan megnevezve (Ksztv., Ptk., stb.) → HAE:3
- Korábbi/hatályos szabályozásra általában, jogszabály név nélkül → HAE:6

NEM:2 vs NEM:3:
- Átfogalmazás: a törvény egy részét mondja más szavakkal
- Kivonatolás: a törvény tartalmát foglalja össze, tömöríti

HAE:8 vs NEM:3 elhatárolás:

Kivonatolás (NEM:3): pusztán összefoglalja vagy tömöríti a törvényszöveget,
nem ad hozzá semmit a megértéshez.

Magyarázat (HAE:8): segíti a megértést, akkor is, ha a törvényből
kiolvasható az információ. Ide tartozik:
- Ha az indokolás összefüggések mentén fűzi össze a szöveget
- Ha strukturáltan mutatja be a szabályozás logikáját
- Ha egy laikus számára érthetőbbé teszi a törvényt
  (pl. hosszabb felsorolás, komplex szabályrendszer magyarázata)
- Ha összekapcsolja a különböző szakaszok tartalmát
- Jellemző fordulatok: "Nem csak X, hanem Y is", "beszélhetünk",
  "tekinthetünk", "ez azt jelenti, hogy", "vagyis", "azaz"

Példák:

NEM:3 (kivonatolás - nem segíti a megértést):
"A törvény meghatározza a kormányzati igazgatási szervek körét."
"A törvény szabályozza a tisztségviselők jogviszonyát."

HAE:8 (magyarázat - segíti a megértést):
"A kormányzati igazgatási szervek köre egyszerre jelent egy bővebb
és egy szűkebb szervi kört a központi államigazgatási szervekhez képest."
"Nem csak szervek, hanem egyes vezetők tekintetében is beszélhetünk
irányításról."
"A három jogviszony-típus eltérő jellegű feladatokat lát el: a politikai
a kormányzati döntéshozatalban, a biztosi a kiemelt projektek vezetésében,
a szakmai pedig a napi operatív működésben vesz részt."
"Valamilyen másik jogintézményre irányadó szabályoktól eltérő módon szabályozza"

A kérdés tehát: "Segíti-e a laikus olvasó megértését, vagy csak
megismétli/tömöríti a törvényt?"

HAE:7 vs HAE:8 elhatárolás:
A hatásvizsgálat (HAE:7) csak akkor, ha VAN BENNE KONKRÉT SZÁM vagy ADAT.
Ha csak általánosan utal hatásra, az magyarázat (HAE:8).

Példák:

HAE:7 (van konkrét adat):
- "Az intézkedés kb. 120 000 vállalkozást érint, évi átlagosan
   15 000 Ft adminisztratív tehercsökkenést eredményezve."
- "A KSH adatai szerint 2019-ben 340 000 egyéni vállalkozó működött,
   közülük mintegy 40%-ot érint a szabályozás."
- "Ausztriában a hasonló szabályozás 15%-os növekedést eredményezett,
   a hatásvizsgálat alapján hasonló eredmények várhatók."
- "A bevezetést követő első évben 25%-kal csökkent az ügyintézési idő."

HAE:8 (nincs konkrét adat, csak általános utalás):
- "Az intézkedés jelentős számú vállalkozást érint és csökkenti
   az adminisztratív terheket."
- "A szabályozás a vállalkozások széles körét érinti."
- "A többi EU tagállamhoz hasonlóan"
- "A V4 országokban is hasonló szabályozás működik"
- "Nemzetközi gyakorlatnak megfelelően"
- "Gazdasági szempontból indokolt"
- "A jogalkalmazást megkönnyíti"

HAE:2 vs NEM:4 elhatárolás:
- HAE:2: Belső utalás, ami ÖSSZHANGBAN VAN a törvényszöveggel
- NEM:4: Az állítás ELLENTMOND a törvénynek, vagy más értéket mond

───────────────────────────────────────────────────────────────────────
KIMENET
───────────────────────────────────────────────────────────────────────

Az indokolás teljes szövegét annotálni kell, minden karakter tartozzon
valamelyik kategóriába.

A válaszban csak az annotált szöveg szerepeljen, tagekkel.
Más szöveg, magyarázat vagy megjegyzés ne legyen.

───────────────────────────────────────────────────────────────────────
KONZISZTENCIA
───────────────────────────────────────────────────────────────────────

Konzisztensen tarsd fent az egész dokumentumban az alkalmazott annotálási szabályokat,
ellenőrizd, hogy mondaton belül is szegmentáltál, ha vegyes a tartalom. Vegyes tartalomnál ne annotálj teljes mondatokat egyben!

Légy következetes a kategóriák alkalmazásában. Ha egy adott típusú
szövegrészt (pl. "a törvény szabályozza...") NEM:3-nak minősítettél,
akkor minden hasonló szerkezetű, logikájú, tartalmú szövegrészt is NEM:3-nak kell
minősítened, ha adott szakasz vonatkozásában a törvényszöveghez viszonyítva ugyanannak a kategóriának felel meg.

Kerülendő: inkonzisztens döntés a határeseteknél.


"""


# ============================================================
# ADATSTRUKTÚRÁK
# ============================================================

@dataclass
class AnnotatedSegment:
    """Egy annotált szegmens"""
    text: str
    category_type: str  # "HAE" vagy "NEM"
    category_num: int
    
    @property
    def char_count(self) -> int:
        return len(self.text)
    
    @property
    def is_hae(self) -> bool:
        return self.category_type == "HAE"
    
    @property
    def category_name(self) -> str:
        if self.is_hae:
            return HAE_CATEGORIES.get(self.category_num, ("?", "#000"))[0]
        else:
            return NEM_CATEGORIES.get(self.category_num, ("?", "#000"))[0]
    
    @property
    def color(self) -> str:
        if self.is_hae:
            return HAE_CATEGORIES.get(self.category_num, ("?", "#000"))[1]
        else:
            return NEM_CATEGORIES.get(self.category_num, ("?", "#000"))[1]


# ============================================================
# ELEMZŐ FUNKCIÓK
# ============================================================

def parse_annotated_text(annotated_text: str) -> List[AnnotatedSegment]:
    """Feldolgozza az annotált szöveget"""
    segments = []
    pattern = r'\[(HAE|NEM):(\d+)\](.*?)\[/\1\]'
    
    for match in re.finditer(pattern, annotated_text, re.DOTALL):
        segments.append(AnnotatedSegment(
            text=match.group(3),
            category_type=match.group(1),
            category_num=int(match.group(2))
        ))
    
    return segments


def create_annotation_prompt(law_text: str, exp_text: str) -> str:
    """Létrehozza az annotálási promptot"""
    prompt = f"""{SYSTEM_PROMPT}

═══════════════════════════════════════════════════════════════════════
TÖRVÉNYSZÖVEG (viszonyítási alap):
═══════════════════════════════════════════════════════════════════════

{law_text}

═══════════════════════════════════════════════════════════════════════
JOGALKOTÓI INDOKOLÁS (ezt annotáld):
═══════════════════════════════════════════════════════════════════════

{exp_text}
"""
    return prompt


def analyze_with_api(law_text: str, exp_text: str, api_key: str) -> Dict:
    """Elemzi a szöveget Claude Opus 4.5-tel"""
    
    client = anthropic.Anthropic(api_key=api_key)
    prompt = create_annotation_prompt(law_text, exp_text)
    
    message = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )
    
    annotated_text = message.content[0].text
    segments = parse_annotated_text(annotated_text)
    
    # Statisztikák számítása
    total_chars = sum(s.char_count for s in segments)
    hae_chars = sum(s.char_count for s in segments if s.is_hae)
    nem_chars = total_chars - hae_chars
    
    hae_pct = (hae_chars / total_chars * 100) if total_chars > 0 else 0
    nem_pct = (nem_chars / total_chars * 100) if total_chars > 0 else 0
    
    # Kategória breakdown
    hae_breakdown = {}
    nem_breakdown = {}
    for seg in segments:
        key = seg.category_num
        if seg.is_hae:
            hae_breakdown[key] = hae_breakdown.get(key, 0) + seg.char_count
        else:
            nem_breakdown[key] = nem_breakdown.get(key, 0) + seg.char_count
    
    return {
        "annotated_text": annotated_text,
        "segments": segments,
        "total_chars": total_chars,
        "hae_chars": hae_chars,
        "nem_chars": nem_chars,
        "hae_pct": hae_pct,
        "nem_pct": nem_pct,
        "hae_breakdown": hae_breakdown,
        "nem_breakdown": nem_breakdown,
    }


# ============================================================
# MEGJELENÍTÉS - LETISZTULT, ELEGÁNS
# ============================================================

def color_box(color: str, size: int = 12) -> str:
    """Színes kocka HTML"""
    border = "1px solid #999" if color in ["#E0E0E0", "#FFEB3B"] else "none"
    return f'<span style="display:inline-block;width:{size}px;height:{size}px;background:{color};border:{border};border-radius:2px;vertical-align:middle;margin-right:4px;"></span>'


def render_annotated_html(segments: List[AnnotatedSegment]) -> str:
    """Színes HTML megjelenítés a szegmensekből"""
    html_parts = []
    
    for seg in segments:
        text = seg.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('\n', '<br>')
        
        bg_color = seg.color
        # Kontraszt
        light_colors = ["#FFEB3B", "#E0E0E0", "#9E9E9E", "#03A9F4", "#4CAF50", "#FF9800"]
        text_color = "#000000" if bg_color in light_colors else "#FFFFFF"
        
        border = "1px solid #bbb" if bg_color == "#E0E0E0" else "none"
        label = f"{seg.category_type}:{seg.category_num}"
        
        html_parts.append(f'''<span style="
            background-color: {bg_color};
            color: {text_color};
            padding: 2px 5px;
            margin: 1px 0;
            border-radius: 3px;
            border: {border};
            display: inline;
            font-size: 14px;
            line-height: 1.9;
        " title="{seg.category_name}"><small style="opacity:0.6;">[{label}]</small> {text}</span>''')
    
    return f'<div style="line-height:2.2;font-family:Georgia,serif;text-align:justify;">{" ".join(html_parts)}</div>'


def render_legend() -> str:
    """Jelmagyarázat HTML - letisztult"""
    html = '<div style="font-size:13px;">'
    
    # HAE
    html += '<div style="margin-bottom:12px;"><strong style="color:#2e7d32;">HAE - Hozzáadott Érték</strong></div>'
    html += '<div style="display:flex;flex-direction:column;gap:4px;margin-bottom:16px;">'
    for num, (name, color) in HAE_CATEGORIES.items():
        html += f'<div style="display:flex;align-items:center;">{color_box(color, 14)}<span style="font-size:12px;">[{num}] {name}</span></div>'
    html += '</div>'
    
    # NEM
    html += '<div style="margin-bottom:12px;"><strong style="color:#c62828;">NEM - Nem Hozzáadott Érték</strong></div>'
    html += '<div style="display:flex;flex-direction:column;gap:4px;">'
    for num, (name, color) in NEM_CATEGORIES.items():
        html += f'<div style="display:flex;align-items:center;">{color_box(color, 14)}<span style="font-size:12px;">[{num}] {name}</span></div>'
    html += '</div>'
    
    html += '</div>'
    return html


def render_breakdown(result: Dict) -> str:
    """Kategória breakdown táblázat - letisztult"""
    html = '<div style="display:flex;gap:30px;flex-wrap:wrap;">'
    
    # HAE
    if result["hae_breakdown"]:
        html += '<div style="flex:1;min-width:280px;">'
        html += '<h4 style="color:#2e7d32;margin-bottom:10px;font-weight:500;">HAE Bontás</h4>'
        html += '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        for num, chars in sorted(result["hae_breakdown"].items()):
            name, color = HAE_CATEGORIES.get(num, ("?", "#000"))
            pct = chars / result["total_chars"] * 100 if result["total_chars"] > 0 else 0
            html += f'''<tr style="border-bottom:1px solid #eee;">
                <td style="padding:6px 4px;">{color_box(color)} HAE:{num}</td>
                <td style="padding:6px 4px;color:#666;">{name}</td>
                <td style="padding:6px 4px;text-align:right;">{chars}</td>
                <td style="padding:6px 4px;text-align:right;font-weight:500;">{pct:.1f}%</td>
            </tr>'''
        html += '</table></div>'
    
    # NEM
    if result["nem_breakdown"]:
        html += '<div style="flex:1;min-width:280px;">'
        html += '<h4 style="color:#c62828;margin-bottom:10px;font-weight:500;">NEM Bontás</h4>'
        html += '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        for num, chars in sorted(result["nem_breakdown"].items()):
            name, color = NEM_CATEGORIES.get(num, ("?", "#000"))
            pct = chars / result["total_chars"] * 100 if result["total_chars"] > 0 else 0
            html += f'''<tr style="border-bottom:1px solid #eee;">
                <td style="padding:6px 4px;">{color_box(color)} NEM:{num}</td>
                <td style="padding:6px 4px;color:#666;">{name}</td>
                <td style="padding:6px 4px;text-align:right;">{chars}</td>
                <td style="padding:6px 4px;text-align:right;font-weight:500;">{pct:.1f}%</td>
            </tr>'''
        html += '</table></div>'
    
    html += '</div>'
    return html


# ============================================================
# STREAMLIT APP
# ============================================================

def main():
    st.set_page_config(
        page_title="HAE Elemző",
        page_icon="§",
        layout="wide"
    )
    
    # CSS - letisztult design
    st.markdown("""
    <style>
        .main > div { padding-top: 2rem; }
        .stTextArea textarea { font-family: Georgia, serif; font-size: 14px; }
        .stButton button { font-weight: 500; }
        h1 { font-weight: 400; letter-spacing: -0.5px; }
        h2, h3 { font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("HAE Elemző")
    st.markdown("Törvény indokolás hozzáadott érték vizsgálat — Claude Opus 4.5")
    
    # Sidebar
    with st.sidebar:
        st.header("Beállítások")
        
        # API kulcs: először Secrets-ből, ha nincs, akkor input
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            api_key = st.text_input(
                "Anthropic API kulcs", 
                type="password", 
                help="Add meg az API kulcsodat. Streamlit Cloud-on használj Secrets-et."
            )
        else:
            st.success("API kulcs betöltve (Secrets)")
        
        st.divider()
        st.header("Jelmagyarázat")
        st.markdown(render_legend(), unsafe_allow_html=True)
    
    # Input mezők
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Törvényszöveg")
        law_text = st.text_area(
            "Másold be a törvény releváns szakaszát",
            height=300,
            placeholder="Pl.: 1. § A Kormány állapítja meg a létszámot...",
            key="law_text",
            label_visibility="collapsed"
        )
    
    with col2:
        st.subheader("Indokolás")
        exp_text = st.text_area(
            "Másold be a hozzá tartozó indokolást",
            height=300,
            placeholder="Pl.: A szabályozás célja, hogy a Kormány határozatban...",
            key="exp_text",
            label_visibility="collapsed"
        )
    
    # Elemzés gomb
    analyze_btn = st.button("Elemzés indítása", type="primary", use_container_width=True)
    
    if analyze_btn:
        if not api_key:
            st.error("Add meg az Anthropic API kulcsodat a bal oldali sávban, vagy állítsd be Secrets-ben.")
        elif not law_text.strip():
            st.warning("Add meg a törvényszöveget.")
        elif not exp_text.strip():
            st.warning("Add meg az indokolást.")
        else:
            with st.spinner("Elemzés folyamatban..."):
                try:
                    result = analyze_with_api(law_text, exp_text, api_key)
                    
                    st.divider()
                    st.header("Eredmények")
                    
                    # Metrikák
                    metric_cols = st.columns(4)
                    with metric_cols[0]:
                        st.metric("Összes karakter", f"{result['total_chars']:,}")
                    with metric_cols[1]:
                        st.metric("HAE", f"{result['hae_pct']:.1f}%", f"{result['hae_chars']:,} kar")
                    with metric_cols[2]:
                        st.metric("NEM", f"{result['nem_pct']:.1f}%", f"{result['nem_chars']:,} kar")
                    with metric_cols[3]:
                        if result['hae_pct'] >= 60:
                            quality = "Jó"
                        elif result['hae_pct'] >= 30:
                            quality = "Közepes"
                        else:
                            quality = "Gyenge"
                        st.metric("Minőség", quality)
                    
                    # Progress bar
                    st.progress(result['hae_pct'] / 100, text=f"HAE: {result['hae_pct']:.1f}%")
                    
                    # Bontás
                    st.subheader("Kategória bontás")
                    st.markdown(render_breakdown(result), unsafe_allow_html=True)
                    
                    # Annotált szöveg
                    st.subheader("Annotált indokolás")
                    st.markdown(render_annotated_html(result["segments"]), unsafe_allow_html=True)
                    
                    # Szegmensek lista
                    with st.expander("Szegmensek listája"):
                        for i, seg in enumerate(result["segments"], 1):
                            st.markdown(f"**{i}. [{seg.category_type}:{seg.category_num}] {seg.category_name}** ({seg.char_count} kar)")
                            st.text(seg.text[:300] + "..." if len(seg.text) > 300 else seg.text)
                            st.divider()
                    
                    # Nyers output
                    with st.expander("Nyers annotált szöveg"):
                        st.code(result["annotated_text"], language=None)
                    
                except anthropic.AuthenticationError:
                    st.error("Hibás API kulcs. Ellenőrizd a kulcsodat.")
                except anthropic.RateLimitError:
                    st.error("API rate limit. Várj egy kicsit és próbáld újra.")
                except Exception as e:
                    st.error(f"Hiba történt: {str(e)}")


if __name__ == "__main__":
    main()
