"""
HAÉ Elemző — Jogalkotói indokolások „hozzáadott értékének” (HAÉ) vizsgálata
Streamlit alkalmazás Claude Opus 4.5 API-val

© 2026 dr. Kiss Rebeka
"""

import streamlit as st
import anthropic
import re
from dataclasses import dataclass
from typing import List, Dict

# ============================================================
# OLDAL KONFIGURÁCIÓ
# ============================================================

st.set_page_config(
    page_title="HAÉ Elemző",
    page_icon="§",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# KATEGÓRIÁK ÉS SZÍNEK
# ============================================================

HAE_CATEGORIES = {
    1: ("Célmeghatározás", "#c0392b", "#fdecea"),
    2: ("Jogszabályon belüli utalás más rendelkezésre", "#7f8c8d", "#f0f0f0"),
    3: ("Kiutalás más jogforrásra", "#2980b9", "#e8f4fd"),
    4: ("Joggyakorlatra való hivatkozás", "#1e8449", "#e8f8f0"),
    5: ("Szakirodalomra való hivatkozás", "#6d4c41", "#f0ebe8"),
    6: ("Összevetés a korábbi szabályozással", "#27ae60", "#eafaf1"),
    7: ("Hatásvizsgálat bemutatása", "#e67e22", "#fef5e7"),
    8: ("Egyéb magyarázatok, példák", "#f1c40f", "#fef9e7"),
}

NEM_CATEGORIES = {
    1: ("Szó szerinti átmásolás", "#8e44ad", "#f4ecf7"),
    2: ("Átfogalmazás", "#1a5276", "#eaf2f8"),
    3: ("Kivonatolás", "#95a5a6", "#f2f3f4"),
    4: ("Normaszövegnek való ellentmondás", "#1c1c1c", "#ebedef"),
}

# ============================================================
# CUSTOM CSS
# ============================================================

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,600;8..60,700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

    .stApp { font-family: 'DM Sans', sans-serif; }
    #MainMenu, footer {visibility: hidden;}
    .stDeployButton {display: none;}
    /* Sidebar nyitó gomb mindig látható maradjon */
    button[data-testid="stSidebarCollapsedControl"],
    button[data-testid="collapsedControl"] {
        visibility: visible !important;
        display: flex !important;
    }

    /* ── Sidebar — enyhén sötétebb mint a fő terület ── */
    section[data-testid="stSidebar"] {
        background: #edf0f4;
        border-right: 1px solid #dce0e6;
    }
    section[data-testid="stSidebar"] * {
        color: #374151 !important;
    }
    section[data-testid="stSidebar"] .stTextInput label {
        color: #1f2937 !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] .stTextInput input {
        color: #1f2937 !important;
        background: #fff !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] .stTextInput input:focus {
        border-color: #4a6fa5 !important;
        box-shadow: 0 0 0 2px rgba(74,111,165,0.15) !important;
    }

    /* ── Sidebar: fejléc igazítva a main headerhez ── */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 28px !important;
    }
    .sidebar-logo {
        font-family: 'Source Serif 4', serif;
        font-size: 22px;
        font-weight: 700;
        color: #1f2937 !important;
        margin-bottom: 24px;
        padding-top: 12px;
    }

    .sidebar-title {
        font-family: 'Source Serif 4', serif;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #6b7280 !important;
        margin: 28px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #d5d9e0;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0;
        font-size: 12.5px;
        line-height: 1.4;
        color: #374151 !important;
    }
    .legend-swatch {
        width: 12px;
        height: 12px;
        min-width: 12px;
        border-radius: 3px;
        display: inline-block;
    }
    .legend-code {
        font-weight: 600;
        font-size: 11px;
        color: #9ca3af !important;
        min-width: 18px;
    }
    .legend-label { color: #374151 !important; }
    .sidebar-model { font-size: 12px; color: #9ca3af !important; }

    /* ── Main header — igazítva a sidebar-hoz ── */
    .main-header {
        font-family: 'Source Serif 4', serif;
        font-size: 38px;
        font-weight: 700;
        color: #1a1f2e;
        margin-bottom: 4px;
        letter-spacing: -0.5px;
        padding-top: 0;
    }
    .main-subtitle {
        font-size: 15px;
        color: #7f8c8d;
        margin-bottom: 36px;
        font-weight: 400;
    }

    /* ── Input section ── */
    .input-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #5d6d7e;
        margin-bottom: 8px;
    }
    .stTextArea textarea {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 13.5px !important;
        line-height: 1.65 !important;
        border: 1.5px solid #e5e8ed !important;
        border-radius: 10px !important;
        padding: 16px !important;
        background: #fafbfc !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .stTextArea textarea:focus {
        border-color: #4a6fa5 !important;
        box-shadow: 0 0 0 3px rgba(74,111,165,0.1) !important;
        background: #fff !important;
    }

    /* ── Analyze button — outline stílus ── */
    div.stButton > button {
        width: 100%;
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        font-size: 15px;
        letter-spacing: 0.5px;
        padding: 14px 32px;
        border-radius: 10px;
        border: 1.5px solid #8d9bab;
        background: #edf0f4;
        color: #2c3e50;
        cursor: pointer;
        transition: all 0.25s ease;
        box-shadow: none;
    }
    div.stButton > button:hover {
        background: #dfe3e9;
        border-color: #5d6d7e;
        box-shadow: 0 2px 8px rgba(44,62,80,0.10);
        transform: translateY(-1px);
    }
    div.stButton > button:active { transform: translateY(0); }

    /* ── Results ── */
    .results-header {
        font-family: 'Source Serif 4', serif;
        font-size: 28px;
        font-weight: 700;
        color: #1a1f2e;
        margin: 48px 0 24px 0;
        padding-top: 32px;
        border-top: 2px solid #e5e8ed;
    }
    .section-header {
        font-family: 'Source Serif 4', serif;
        font-size: 20px;
        font-weight: 600;
        color: #1a1f2e;
        margin: 36px 0 16px 0;
    }

    /* ── Metric cards — HAÉ/NEM kiemeltek ── */
    .metric-row {
        display: flex;
        gap: 16px;
        margin-bottom: 28px;
    }
    .metric-card {
        flex: 1;
        background: #fff;
        border: 1px solid #e5e8ed;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-card.card-hae {
        background: #f4fbf7;
        border: 1.5px solid #8ed4ab;
        box-shadow: 0 1px 4px rgba(39,174,96,0.08);
    }
    .metric-card.card-nem {
        background: #fef7f5;
        border: 1.5px solid #f0a99e;
        box-shadow: 0 1px 4px rgba(231,76,60,0.07);
    }
    .metric-value {
        font-family: 'Source Serif 4', serif;
        font-size: 26px;
        font-weight: 700;
        color: #1a1f2e;
        line-height: 1.1;
    }
    .metric-label {
        font-size: 11.5px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #95a5a6;
        margin-top: 6px;
        font-weight: 500;
    }

    /* ── Quality badge (4 fokozat) ── */
    .quality-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .quality-excellent {
        background: #d5f5e3;
        color: #1a8c4e;
        border: 1px solid #82e0aa;
    }
    .quality-good {
        background: #eafaf1;
        color: #1e8449;
        border: 1px solid #a9dfbf;
    }
    .quality-medium {
        background: #fef9e7;
        color: #b7950b;
        border: 1px solid #f9e79f;
    }
    .quality-poor {
        background: #fdecea;
        color: #c0392b;
        border: 1px solid #f5b7b1;
    }

    /* ── Progress bar ── */
    .progress-container { margin: 20px 0 32px 0; }
    .progress-labels {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 13px;
        font-weight: 600;
    }
    .progress-hae-label { color: #27ae60; }
    .progress-nem-label { color: #e74c3c; }
    .progress-bar-bg {
        height: 10px;
        background: #fdecea;
        border-radius: 5px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #27ae60, #2ecc71);
        border-radius: 5px;
        transition: width 0.8s ease;
    }

    /* ── Category breakdown ── */
    .breakdown-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
        margin: 20px 0;
    }
    .breakdown-section {
        background: #fff;
        border: 1px solid #e5e8ed;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .breakdown-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid #e5e8ed;
    }
    .breakdown-title.hae { color: #27ae60; }
    .breakdown-title.nem { color: #e74c3c; }

    .cat-row {
        display: flex;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #f5f6f8;
        font-size: 13px;
    }
    .cat-row:last-child { border-bottom: none; }
    .cat-swatch { width: 10px; height: 10px; min-width: 10px; border-radius: 2px; margin-right: 10px; }
    .cat-code { font-weight: 600; color: #7f8c8d; font-size: 11px; min-width: 40px; margin-right: 8px; }
    .cat-name { flex: 1; color: #2c3e50; }
    .cat-chars { font-weight: 500; color: #7f8c8d; font-size: 12px; min-width: 60px; text-align: right; margin-right: 12px; }
    .cat-pct { font-weight: 700; min-width: 48px; text-align: right; font-size: 13px; }
    .cat-bar-bg { width: 60px; height: 4px; background: #f0f0f0; border-radius: 2px; margin-left: 12px; overflow: hidden; }
    .cat-bar-fill { height: 100%; border-radius: 2px; }

    /* ── Annotated text ── */
    .annotated-container {
        background: #fff;
        border: 1px solid #e5e8ed;
        border-radius: 12px;
        padding: 28px 32px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        line-height: 1.85;
        font-size: 14px;
        color: #2c3e50;
    }
    .ann-segment {
        padding: 2px 1px;
        border-radius: 3px;
        border-bottom: 2.5px solid transparent;
        transition: all 0.15s ease;
        cursor: default;
    }
    .ann-segment:hover { filter: brightness(0.95); }
    .ann-tag {
        font-size: 9.5px;
        font-weight: 700;
        padding: 1px 5px;
        border-radius: 3px;
        margin-right: 2px;
        vertical-align: middle;
        letter-spacing: 0.3px;
        color: #fff;
    }

    /* ── Segment list ── */
    .seg-list-item {
        display: flex;
        gap: 12px;
        padding: 12px 16px;
        border-bottom: 1px solid #f5f6f8;
        font-size: 13px;
        line-height: 1.5;
    }
    .seg-list-item:last-child { border-bottom: none; }
    .seg-list-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        white-space: nowrap;
        height: fit-content;
        margin-top: 2px;
    }
    .seg-list-text { color: #5d6d7e; flex: 1; }
    .seg-list-chars { color: #95a5a6; font-size: 11px; white-space: nowrap; margin-top: 2px; }

    /* ── Footer ── */
    .app-footer {
        text-align: center;
        padding: 40px 0 20px 0;
        font-size: 12px;
        color: #bdc3c7;
        border-top: 1px solid #e5e8ed;
        margin-top: 48px;
    }

    /* ── Streamlit overrides ── */
    div[data-testid="stExpander"] {
        border: 1px solid #e5e8ed !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    .stSpinner > div { border-color: #2c3e50 transparent transparent !important; }

    @media (max-width: 768px) {
        .metric-row { flex-direction: column; }
        .breakdown-grid { grid-template-columns: 1fr; }
        .main-header { font-size: 28px; }
    }
</style>
"""


# ============================================================
# SYSTEM PROMPT — EREDETI
# ============================================================

SYSTEM_PROMPT = """
────────────────────────────────────────────────────
ALAPKÉRDÉS
────────────────────────────────────────────────────
Minden szövegrésznél döntsd el: magyaráz-e az indokolás, vagy csak megismétli a törvényszöveget más szavakkal?

Magyarázat: segíti a megértést, kontextust ad, indokol, értékel, vagy olyan információt közöl, ami a törvényszövegből nem olvasható ki, de ahhoz közvetlenül kapcsolódik.

Nem magyarázat: ha más szavakkal mondja ugyanazt, amit a törvény, vagy összefoglalja annak tartalmát.

────────────────────────────────────────────────────
HOZZÁADOTT ÉRTÉK KATEGÓRIÁK - jelölés: [HAE:n]...[/HAE]
────────────────────────────────────────────────────

[HAE:1] CÉLMEGHATÁROZÁS
A törvény vagy a konkrét szakasz céljának, a jogalkotó szándékának, a szabályozás céljának explicit megfogalmazása.

Jellemző fordulatok:
	"a törvény célja, hogy"
	"e szakasz célja"
	"a szabályozás célja"
	"e rendelkezés célja"
	"a jogalkotó szándéka"
	"célul tűzi ki"

NEM ide tartozik (ezek HAE:8 – egyéb magyarázat):
	"X érdekében Y-t tesz lehetővé" (ez magyarázat, de nem célmeghatározás)
	"a feladatok ellátása érdekében" (ha nem szerepel a törvényben, akkor ez kontextus, további magyarázat, de nem feltétlenül célmeghatározás)
	"lehetőséget ad arra, hogy" (ez az, amit a törvény tesz, de nem célmeghatározás)
	"megteremti a lehetőségét annak, hogy" (ez eredmény, de nem célmeghatározás)

Ha az indokolás azt írja le „zanzásítva”, hogy mit tesz lehetővé a törvény, az kivonatolás (NEM:3) vagy átfogalmazás (NEM:2), nem célmeghatározás.

Példa – HAE:1 (valódi célmeghatározás):
	"A törvény célja a gyülekezési jog gyakorlásának szabályozása."
	"A jogalkotó szándéka a korábbi hiányosságok orvoslása."

Példa – HAE:8 (egyéb magyarázat, NEM célmeghatározás):
	"A közbiztonság érdekében szükségessé válhat az ellenőrzés."
	"A feladatok ellátása érdekében elengedhetetlen a jelenlét."
	"Az együttműködési kötelezettség garantálja a békés jelleg biztosítását." (ez utóbbi azért HAE:8, mert: leírja az eredményt (mit garantál), magyarázza a szabály funkcióját, de NEM mondja ki, hogy mi lenne "a törvény célja" vagy "a jogalkotó szándéka", adott jogintézmény, szakasz, bevezetett jogintézmény stb.)

[HAE:2] BELSŐ UTALÁS (ugyanezen törvényen belüli kereszthivatkozás)
Utalás a törvény szövegének más rendelkezéseire.

Példák: 
	"az 51. § szerinti szabályokat alkalmazni kell",
	"a fenti szabályokkal összhangban", 
	"e törvény 10. §-a alapján", "
	"a javaslat 2. § (2) bekezdése egyértelművé teszi"

[HAE:3] KÜLSŐ JOGFORRÁSRA HIVATKOZÁS (más jogszabályra, irányelvre stb. utalás)
Konkrétan megnevezett más jogszabályra való hivatkozás (de akár konkrét jogszabály szám nélkül).

Példák: 
	"az Alaptörvény 15. cikk (2) bekezdése szerint",
	"a 2010. évi XLIII. törvény (Ksztv.) szabályozását átvéve",
	"a Ksztv. rendelkezéseit átemelve", 
	"a Ptk. szerint"
	"a jogalkotásról szóló törvény alapján",
	"a kereskedelemről szóló törvényben meghatározott"

Ide tartoznak az alacsonyabb jogforrásokra (korm. rendeletekre) való utalások is.

Példák: 
	"a veszélyhelyzet kihirdetéséről szóló 478/2020. (XI. 3.) Korm. rendelet szerinti"
	"a zenés, táncos gyűlések működésének biztonságosabbá tételéről szóló 23/2011. (III. 8.) Korm. rendelet"

Fontos, hogy salátatörvény jellegű (sok törvényt egyszerre módosító) törvényeknél pusztán azért, mert az indokolás szövegében benne van sok más jogszabály neve, nem HAE, ha pont azt a jogszabályt módosítja az adott törvény.

[HAE:4] BÍRÓSÁGI DÖNTÉSEK, JOGGYAKORLAT ÉS AB HATÁROZATOK
Bírósági döntésekre, AB határozatokra, EJEB döntésére, joggyakorlatra, bírósági gyakorlatra, konkrét ítéletre való utalás.

Ide tartozik: joggyakorlat alapján levont olyan következtetés, ami közvetlen utalást tartalmaz valamilyen bírósági álláspontra, jogalkalmazói visszajelzés alapján történő jogalkotásra való utalás, bíróságok álláspontjának kifejtése, arra való konkrét utalással.

Példák: 
	"a bírói gyakorlattal egyezően", 
	„az AB határozat alapján”, 
	"általános joggyakorlattal egyezően"

NEM ide tartozik: alapvető jogokra, alapelvekre való általános utalás.

[HAE:5] SZAKIRODALOM, KUTATÁSI EREDMÉNY
Tudományos művekre, szakmai jelentésekre való hivatkozás.

Példák: 
	"a KSH jelentése szerint", 
	"az OECD ajánlásaival összhangban", 
	"Vékás Lajos professzor munkái", 
	"a szakirodalom álláspontját követve", 
	"a szakirodalmi álláspont alapján"

[HAE:6] ÖSSZEVETÉS KORÁBBI SZABÁLYOZÁSSAL 
A korábbi és új szabályozás viszonyának bemutatása, konkrét jogszabály megnevezése nélkül.

Ide tartozik, ha az indokolás jelzi, hogy valamely rendelkezés "új", "bevezet", "meghonosít", "kivezet", "megszüntet", "rendelkezést fenntart", "változtat", "eltörli" – ezek korábbi állapothoz való viszonyítást írnak le.

Példák: 
	"a korábbi szabályozással egyezően", 
	"a hatályos szabályozást átvéve", 
	"új eleme a törvénynek", 
	"korábban nem volt", 
	"közjogi hagyományoknak megfelelően", 
	"fontos változás", 
	"vonatkozó rendelkezések elhagyásra kerültek", 
	"továbbra is", 
	"adott rendelkezés kivezetésével"

[HAE:7] HATÁSVIZSGÁLAT BEMUTATÁSA
A szabályozás hatásainak bemutatása jellemzően konkrét adatokkal, tényekkel alátámasztva. Előzetes hatásvizsgálatra, kutatásra, felmérésre való hivatkozás eredményekkel.

Ide tartozik, ha az indokolás tartalmazza az alábbiakat:
	Érintett csoportok létszáma (fő, db, vállalkozás)
     Pl.: "kb. 50 000 vállalkozást érint", "1 millió nyugdíjast érint"
	Költségvetési / gazdasági hatás konkrét összeggel (Ft)
     Pl.: "évi 2 milliárd Ft megtakarítás", "500 millió Ft többletkiadás"
	Adminisztratív terhek változása számszerűsítve (Ft, óra, %)
     Pl.: "évi 10 000 Ft/vállalkozás tehercsökkenés", "30%-kal kevesebb ügyintézési idő"
	 Foglalkoztatási hatás létszámmal
     Pl.: "200 új munkahely", "50 fős létszámcsökkenés"
	 Más országok tapasztalata konkrét eredményekkel
     Pl.: "Ausztriában 15%-os növekedést eredményezett, a hatásvizsgálat alapján hasonló hatások várhatók Magyarországon is a szabályozás bevezetésével"
	Konkrét időtáv
     Pl.: "2020-2024 között", "a bevezetést követő 4 évben"

NEM ide tartozik (ezek HAE:8):
	"adminisztratív terheket csökkent" (szám nélkül)
	"a jogalkalmazást megkönnyíti" (konkrétum nélkül)
	"költségvetési hatása minimális" (összeg nélkül)
	"a többi EU tagállamhoz hasonlóan" (eredmény nélkül)
	"gazdasági szempontból indokolt" (adat nélkül)
	"széles társadalmi réteget érint" (létszám nélkül)

[HAE:8] EGYÉB MAGYARÁZAT ÉS PÉLDÁK
Indokolás, érvelés, háttérinformáció, összefüggés-feltárás.

Példák: 
	"tekintettel arra, hogy", 
	"figyelemmel arra", 
	"mivel",
	"ezért szükséges", 
	"ugyanis", 
	"ennek indoka"

Ide tartozik még:
	A törvényben nem szereplő konkrét példák.
	Általános hatásokra utalás konkrét adat nélkül ("csökkenti a terheket", "megkönnyíti a jogalkalmazást")
	Nemzetközi összehasonlítás adatok nélkül ("EU tagállamokhoz hasonlóan", "nemzetközi gyakorlatnak megfelelően")

────────────────────────────────────────────────────
NEM HOZZÁADOTT ÉRTÉK KATEGÓRIÁK - jelölés: [NEM:n]...[/NEM]
────────────────────────────────────────────────────

[NEM:1] SZÓ SZERINTI ÁTMÁSOLÁS 
A törvényszöveg változtatás nélküli átvétele.

[NEM:2] ÁTFOGALMAZÁS (parafrázis)
 A törvényszöveg más szórenddel, szinonimákkal való visszaadása, amely nem ad új információt.

[NEM:3] KIVONATOLÁS
A törvényszöveg tömörítése, összefoglalása magyarázat nélkül.

Jellemző formulák: 
	"a törvény rendelkezik", 
	"meghatározza",
	"szabályozza", 
	"rögzíti", 
	"kimondja"

Szintén ide tartozik, ha az indokolás csak annyit mond – de nem fejti ki jobban a mögöttes okokat vagy egyéb részleteket –, hogy "hatályon kívül helyező rendelkezések", "jogtechnikai jellegű pontosítás", " felhatalmazó rendelkezések", "technikai jellegű szövegcserés módosítás", "terminológiai pontosítást tartalmaz", "jogharmonizációs záradékot tartalmaz", "nyelvhelyességi korrekció", "hatályon kívül helyező rendelkezéseket tartalmaz", "sarkalatossági záradék kiegészítése", "átmeneti rendelkezés". És ezekhez hasonló tartalomjegyzék szerű kivonatolások.

[NEM:4] HIBÁS INDOKOLÁS 

Ide tartozik:
	Ellentmondás: az indokolás tartalmilag ellentmond a törvényszövegnek
	Normaszöveghez nem kapcsolódó magyarázat: az indokolás nem a hivatkozott szakaszhoz kapcsolódik, hanem más rendelkezéseket ismertet, tartalmilag nincsen köze a hozzá tartozó törvényszöveghez.
	Olyan többlet információk, amik nem magyarázatok, hanem túllépnek a normaszövegen, az abban található állításokból egyáltalán nem következnek.

Példa: 
normaszöveg: „(1) A teljes munkaidőben foglalkoztatott kormánytisztviselő írásbeli kérelmére a kinevezésben részmunkaidőt kell kikötni, ha a kormánytisztviselő a kérelem benyújtásakor gyermeke harmadik életéve betöltéséig – a gyermek gondozása céljából – fizetés nélküli szabadságra jogosult. A részmunkaidőben történő foglalkoztatás esetén a kormánytisztviselő heti munkarendje – a kormánytisztviselő kérelmére – egyenlőtlen munkaidő-beosztással meghatározható.
(2) A kormánytisztviselőnek a munkaidő egyenlőtlen beosztására vonatkozó (1) bekezdés szerinti kérelme csak abban az esetben tagadható meg, ha az a munkáltatói jogkör gyakorlója számára lényegesen nagyobb munkaszervezési terhet jelentene. A munkáltatói jogkör gyakorlója köteles írásban megindokolni a kérelem megtagadását.
(3) A részmunkaidő kikötése
a) a fizetés nélküli szabadság megszűnését követő naptól,
b) ha a kormánytisztviselőnek betegsége vagy a személyét érintő más elháríthatatlan akadály esetén az akadályoztatás megszűnésétől számított harminc napon belül ki kell adni alapszabadságát, a szabadság leteltét követő naptól
hatályos.
(4) A (3) bekezdés b) pontjában foglaltak alkalmazása esetén – a felek eltérő megállapodása hiányában – a rendes szabadság kiadását a fizetés nélküli szabadság lejártát követő első munkanapon meg kell kezdeni. Eltérő megállapodás esetén a rendes szabadság kiadását a fizetés nélküli szabadság lejártát követő harminc napon belül meg kell kezdeni.
(5) A kérelmet az (1) bekezdés szerinti fizetés nélküli szabadság igénybevételének megszűnése előtt legalább hatvan nappal kell a hivatali szervezet vezetőjével közölni. A kérelemben a kormánytisztviselő köteles tájékoztatni a hivatali szervezet vezetőjét
a) a fizetés nélküli szabadság igénybevételére jogosító gyermeke harmadik életéve betöltésének időpontjáról, továbbá
b) ha egyenlőtlen munkaidő-beosztásban kíván dolgozni, a munkaidő-beosztásra vonatkozó javaslatáról.
(6) Az (1) bekezdés szerinti kérelem alapján kikötött részmunkaidőben a munkáltatói jogkör gyakorlója a kormánytisztviselőt
a) a kérelem szerinti időpontig, de
b) legfeljebb a gyermek hároméves koráig, három vagy több gyermeket nevelő kormánytisztviselő esetén a gyermek ötéves koráig
köteles foglalkoztatni. Ezt követően a kormánytisztviselő munkaidejét a kérelem benyújtása előtti mérték szerint kell megállapítani.
(7) Az (1)–(6) bekezdés nem alkalmazható a vezetői álláshelyen foglalkoztatott kormánytisztviselő tekintetében.”
indokolás: "A törvény a teljes munkaidőben foglalkoztatott kormánytisztviselő írásbeli kérelmére a kinevezésben heti húszórás részmunkaidőt kikötését teszi lehetővé, ha a kormánytisztviselő a kérelem benyújtásakor gyermeke harmadik életéve betöltéséig - a gyermek gondozása céljából - fizetés nélküli szabadságra jogosult."
ellentmondás: „húszórás” - de csak ez a kifejezés, mondaton belül kell szegmentálni, ha indokolt.

────────────────────────────────────────────────────
SZEGMENTÁLÁSI SZABÁLYOK
────────────────────────────────────────────────────

Kötelező mondaton belül is szegmentálni, ha vegyes a tartalom. 
Ezekben az esetekben ne annotálj teljes mondatokat egyben!

Példa – beékelt HAE:6: 
"A törvény – a hatályos szabályozást átvéve – rendelkezik a testületekről."
Helyes annotáció:
[NEM:3] A törvény – [/NEM] [HAE:6] a hatályos szabályozást átvéve [/HAE] [NEM:3] – rendelkezik a testületekről. [/NEM]

Példa – beékelt HAE:3:
"A törvény – átemelve a Ksztv. rendelkezéseit – meghatározza a hatásköröket."
Helyes annotáció:
[NEM:3] A törvény – [/NEM] [HAE:3] átemelve a Ksztv. rendelkezéseit [/HAE] [NEM:3] – meghatározza a hatásköröket. [/NEM]
 
Példa – célmeghatározás HAE:1 + kivonatolás NEM3:
"A törvény a szervi és személyi megközelítés egységét tűzi ki célul, szabályozza a szervek jogállását."
Helyes annotáció:
[HAE:1] A törvény a szervi és személyi megközelítés egységét tűzi ki célul, [/HAE] [NEM:3] szabályozza a szervek jogállását. [/NEM]

Figyelj a gondolatjelek, zárójelek közötti beszúrásokra. Ezek gyakran külön kategóriába tartoznak!

────────────────────────────────────────────────────
ELHATÁROLÁSOK
────────────────────────────────────────────────────

HAE:2 vs HAE:3 vs HAE:6:
	Ugyanezen törvény szakaszára utal → HAE:2
	Más jogszabályra, konkrétan megnevezve (Ksztv., Ptk., stb.) → HAE:3
	Korábbi/hatályos szabályozásra általában, jogszabály megnevezése nélkül → HAE:6

NEM:2 vs NEM:3:
	Átfogalmazás (NEM:2): a törvény egy részét mondja más szavakkal
	Kivonatolás (NEM:3): a törvény tartalmát foglalja össze, tömöríti

HAE:8 vs NEM:3 elhatárolás:
	Kivonatolás (NEM:3): pusztán összefoglalja vagy tömöríti a törvényszöveget, nem ad hozzá semmit a megértéshez.
	Magyarázat (HAE:8): segíti a megértést, akkor is, ha a törvényből kiolvasható az információ. 
Ide tartozik:
o	Ha az indokolás összefüggések mentén fűzi össze a szöveget
o	Ha strukturáltan mutatja be a szabályozás logikáját
o	Ha egy laikus számára érthetőbbé teszi a törvényt (pl. hosszabb felsorolás, komplex szabályrendszer magyarázata)
o	Ha összekapcsolja a különböző szakaszok tartalmát
o	Jellemző fordulatok: "Nem csak X, hanem Y is", "beszélhetünk", "tekinthetünk", "ez azt jelenti, hogy", "vagyis", "azaz"

Példák:

NEM:3 (kivonatolás – nem segíti a megértést):
	"A törvény meghatározza a kormányzati igazgatási szervek körét."
	"A törvény szabályozza a tisztségviselők jogviszonyát."

HAE:8 (magyarázat – segíti a megértést):
	"A kormányzati igazgatási szervek köre egyszerre jelent egy bővebb
	és egy szűkebb szervi kört a központi államigazgatási szervekhez képest."
	"Nem csak szervek, hanem egyes vezetők tekintetében is beszélhetünk
	irányításról."
	"A három jogviszony-típus eltérő jellegű feladatokat lát el: a politikai
	a kormányzati döntéshozatalban, a biztosi a kiemelt projektek vezetésében,
	a szakmai pedig a napi operatív működésben vesz részt."
	"Valamilyen másik jogintézményre irányadó szabályoktól eltérő módon szabályozza"

A kérdés tehát: segíti-e a laikus olvasó megértését, vagy csak megismétli/tömöríti a törvényt?

HAE:7 vs HAE:8 elhatárolás:
A hatásvizsgálat (HAE:7) csak akkor, ha van benne konkrét adat vagy tényekkel való alátámasztás.
Ha csak általánosan utal valamilyen hatásra, az magyarázat (HAE:8).

Példák:

HAE:7 (van konkrét adat):
	"Az intézkedés kb. 120 000 vállalkozást érint, évi átlagosan 15 000 Ft adminisztratív tehercsökkenést eredményezve."
	"A KSH adatai szerint 2019-ben 340 000 egyéni vállalkozó működött, közülük mintegy 40%-ot érint a szabályozás."
	"Ausztriában a hasonló szabályozás 15%-os növekedést eredményezett, a hatásvizsgálat alapján hasonló eredmények várhatók."
	"A bevezetést követő első évben 25%-kal csökkent az ügyintézési idő."

HAE:8 (nincs konkrét adat, tény, hatásvizsgálat mögötte, csak általános utalás):
	"Az intézkedés jelentős számú vállalkozást érint és csökkenti az adminisztratív terheket."
	"A szabályozás a vállalkozások széles körét érinti."
	"A többi EU tagállamhoz hasonlóan"
	"A V4 országokban is hasonló szabályozás működik"
	"Nemzetközi gyakorlatnak megfelelően"
	"Gazdasági szempontból indokolt"
	"A jogalkalmazást megkönnyíti"

HAE:2 vs NEM:4 elhatárolás:
	HAE:2: Belső utalás, ami ÖSSZHANGBAN VAN a törvényszöveggel
	NEM:4: Az állítás ELLENTMOND a törvénynek, vagy más értéket mond

────────────────────────────────────────────────────
KIMENET
────────────────────────────────────────────────────

Az indokolás teljes szövegét annotálni kell, minden karakter tartozzon valamelyik kategóriába.

A válaszban csak az annotált szöveg szerepeljen, a megfelelő jelölésekkel, más szöveg, magyarázat vagy megjegyzés ne legyen.

────────────────────────────────────────────────────
KONZISZTENCIA
────────────────────────────────────────────────────

Konzisztensen tartsd fenn az egész dokumentum egységben az alkalmazott annotálási szabályokat.

Légy következetes a kategóriák alkalmazásában. Ha egy adott típusú szövegrészt (pl. "a törvény szabályozza...") NEM:3-nak minősítettél, akkor minden hasonló szerkezetű, logikájú, tartalmú szövegrészt is NEM:3-nak kell minősítened, ha adott szakasz vonatkozásában a törvényszöveghez viszonyítva ugyanannak a kategóriának felel meg.

Ellenőrizd, hogy mondaton belül is szegmentáltál, ha vegyes a tartalom. Vegyes tartalomnál ne annotálj teljes mondatokat egyben!

Kerülendő: inkonzisztens döntés a határeseteknél.

"""



# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Segment:
    category_type: str
    category_num: int
    text: str
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.text)

    @property
    def display_type(self) -> str:
        return "HAÉ" if self.category_type == "HAE" else "NEM"

    @property
    def label(self) -> str:
        return f"{self.display_type}:{self.category_num}"

    @property
    def color(self) -> str:
        cats = HAE_CATEGORIES if self.category_type == "HAE" else NEM_CATEGORIES
        return cats.get(self.category_num, ("", "#888", "#f0f0f0"))[1]

    @property
    def bg_color(self) -> str:
        cats = HAE_CATEGORIES if self.category_type == "HAE" else NEM_CATEGORIES
        return cats.get(self.category_num, ("", "#888", "#f0f0f0"))[2]

    @property
    def name(self) -> str:
        cats = HAE_CATEGORIES if self.category_type == "HAE" else NEM_CATEGORIES
        return cats.get(self.category_num, ("Ismeretlen",))[0]


# ============================================================
# PARSING
# ============================================================

def parse_annotated_text(text: str) -> List[Segment]:
    pattern = r'\[(HAE|NEM):(\d+)\](.*?)\[/\1\]'
    segments = []
    for match in re.finditer(pattern, text, re.DOTALL):
        cat_type = match.group(1)
        cat_num = int(match.group(2))
        content = match.group(3).strip()
        if content:
            segments.append(Segment(category_type=cat_type, category_num=cat_num, text=content))
    return segments


def compute_stats(segments: List[Segment]) -> Dict:
    total_chars = sum(s.char_count for s in segments)
    hae_chars = sum(s.char_count for s in segments if s.category_type == "HAE")
    nem_chars = sum(s.char_count for s in segments if s.category_type == "NEM")

    hae_pct = (hae_chars / total_chars * 100) if total_chars > 0 else 0
    nem_pct = (nem_chars / total_chars * 100) if total_chars > 0 else 0

    hae_breakdown = {}
    for num, (name, color, bg) in HAE_CATEGORIES.items():
        chars = sum(s.char_count for s in segments if s.category_type == "HAE" and s.category_num == num)
        pct = (chars / total_chars * 100) if total_chars > 0 else 0
        if chars > 0:
            hae_breakdown[num] = {"name": name, "chars": chars, "pct": pct, "color": color}

    nem_breakdown = {}
    for num, (name, color, bg) in NEM_CATEGORIES.items():
        chars = sum(s.char_count for s in segments if s.category_type == "NEM" and s.category_num == num)
        pct = (chars / total_chars * 100) if total_chars > 0 else 0
        if chars > 0:
            nem_breakdown[num] = {"name": name, "chars": chars, "pct": pct, "color": color}

    # 4 fokozatú minőségi besorolás
    if hae_pct >= 70:
        quality = ("Kiváló", "quality-excellent")
    elif hae_pct >= 50:
        quality = ("Jó", "quality-good")
    elif hae_pct >= 30:
        quality = ("Közepes", "quality-medium")
    else:
        quality = ("Gyenge", "quality-poor")

    return {
        "total_chars": total_chars,
        "hae_chars": hae_chars,
        "nem_chars": nem_chars,
        "hae_pct": hae_pct,
        "nem_pct": nem_pct,
        "hae_breakdown": hae_breakdown,
        "nem_breakdown": nem_breakdown,
        "quality": quality,
    }


# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">§ HAÉ Elemző</div>', unsafe_allow_html=True)

        api_key = st.text_input(
            "Anthropic API kulcs",
            type="password",
            placeholder="sk-ant-api03-...",
            help="Add meg saját Anthropic API kulcsodat. Kulcsot a console.anthropic.com felületen generálhatsz. A kulcs nem kerül tárolásra.",
        )
        if not api_key:
            try:
                api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
            except Exception:
                api_key = ""

        st.markdown('<div class="sidebar-title">HAÉ — „hozzáadott érték”</div>', unsafe_allow_html=True)
        for num, (name, color, bg) in HAE_CATEGORIES.items():
            st.markdown(f'<div class="legend-item"><span class="legend-swatch" style="background:{color};"></span><span class="legend-code">{num}</span><span class="legend-label">{name}</span></div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-title">NEM — nem „hozzáadott érték”</div>', unsafe_allow_html=True)
        for num, (name, color, bg) in NEM_CATEGORIES.items():
            st.markdown(f'<div class="legend-item"><span class="legend-swatch" style="background:{color};"></span><span class="legend-code">{num}</span><span class="legend-label">{name}</span></div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-title">Modell</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-model">Claude Opus 4.5</div>', unsafe_allow_html=True)

    return api_key


def render_metrics(stats: Dict):
    quality_text, quality_class = stats["quality"]
    st.markdown(f'''
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-value">{stats["total_chars"]:,}</div>
                <div class="metric-label">Összes karakter</div>
            </div>
            <div class="metric-card card-hae">
                <div class="metric-value" style="color:#1e8449">{stats["hae_pct"]:.1f}%</div>
                <div class="metric-label">HAÉ („hozzáadott érték”)</div>
            </div>
            <div class="metric-card card-nem">
                <div class="metric-value" style="color:#c0392b">{stats["nem_pct"]:.1f}%</div>
                <div class="metric-label">NEM (nem „hozzáadott érték”)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value"><span class="quality-badge {quality_class}">{quality_text}</span></div>
                <div class="metric-label">Minőség</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)


def render_progress_bar(stats: Dict):
    st.markdown(f'''
        <div class="progress-container">
            <div class="progress-labels">
                <span class="progress-hae-label">HAÉ {stats["hae_pct"]:.1f}% — {stats["hae_chars"]:,} kar</span>
                <span class="progress-nem-label">NEM {stats["nem_pct"]:.1f}% — {stats["nem_chars"]:,} kar</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:{stats["hae_pct"]:.1f}%"></div>
            </div>
        </div>
    ''', unsafe_allow_html=True)


def render_breakdown(stats: Dict):
    hae_rows = ""
    for num, data in stats["hae_breakdown"].items():
        max_pct = max((d["pct"] for d in stats["hae_breakdown"].values()), default=1)
        bar_w = min(data["pct"] / max_pct * 100, 100) if max_pct > 0 else 0
        hae_rows += f'<div class="cat-row"><span class="cat-swatch" style="background:{data["color"]}"></span><span class="cat-code">HAÉ:{num}</span><span class="cat-name">{data["name"]}</span><span class="cat-chars">{data["chars"]:,} kar</span><span class="cat-pct" style="color:{data["color"]}">{data["pct"]:.1f}%</span><span class="cat-bar-bg"><span class="cat-bar-fill" style="width:{bar_w:.0f}%; background:{data["color"]}"></span></span></div>'

    nem_rows = ""
    for num, data in stats["nem_breakdown"].items():
        max_pct = max((d["pct"] for d in stats["nem_breakdown"].values()), default=1)
        bar_w = min(data["pct"] / max_pct * 100, 100) if max_pct > 0 else 0
        nem_rows += f'<div class="cat-row"><span class="cat-swatch" style="background:{data["color"]}"></span><span class="cat-code">NEM:{num}</span><span class="cat-name">{data["name"]}</span><span class="cat-chars">{data["chars"]:,} kar</span><span class="cat-pct" style="color:{data["color"]}">{data["pct"]:.1f}%</span><span class="cat-bar-bg"><span class="cat-bar-fill" style="width:{bar_w:.0f}%; background:{data["color"]}"></span></span></div>'

    st.markdown(f'''
        <div class="breakdown-grid">
            <div class="breakdown-section">
                <div class="breakdown-title hae">HAÉ — „hozzáadott érték” — Bontás</div>
                {hae_rows or '<div style="color:#bdc3c7; font-size:13px; padding:8px 0;">Nincs HAÉ kategória</div>'}
            </div>
            <div class="breakdown-section">
                <div class="breakdown-title nem">NEM — nem „hozzáadott érték” — Bontás</div>
                {nem_rows or '<div style="color:#bdc3c7; font-size:13px; padding:8px 0;">Nincs NEM kategória</div>'}
            </div>
        </div>
    ''', unsafe_allow_html=True)


def render_annotated_text(segments: List[Segment]):
    html_parts = []
    for seg in segments:
        escaped = seg.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        tag = f'<span class="ann-tag" style="background:{seg.color};">{seg.label}</span>'
        html_parts.append(f'<span class="ann-segment" style="background:{seg.bg_color}; border-bottom-color:{seg.color};">{tag}{escaped}</span>')
    st.markdown(f'<div class="annotated-container">{" ".join(html_parts)}</div>', unsafe_allow_html=True)


def render_segment_list(segments: List[Segment]):
    html = []
    for seg in segments:
        escaped = seg.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        preview = escaped[:200] + "..." if len(escaped) > 200 else escaped
        html.append(f'<div class="seg-list-item"><span class="seg-list-badge" style="background:{seg.bg_color}; color:{seg.color}; border:1px solid {seg.color};">{seg.label}</span><span class="seg-list-text">{preview}</span><span class="seg-list-chars">{seg.char_count:,} kar</span></div>')
    return "".join(html)


# ============================================================
# MAIN
# ============================================================

def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    api_key = render_sidebar()

    st.markdown('<div class="main-header">„Hozzáadott Érték” Elemző</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">Jogalkotói indokolások „hozzáadott értékének” (HAÉ) vizsgálata</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown('<div class="input-label">Normaszöveg</div>', unsafe_allow_html=True)
        law_text = st.text_area("law", height=280, placeholder="Másold be ide a releváns normaszöveg-szakasz(oka)t...", label_visibility="collapsed")
    with col2:
        st.markdown('<div class="input-label">Indokolás</div>', unsafe_allow_html=True)
        explanation_text = st.text_area("explanation", height=280, placeholder="Másold be ide a részletes indokolás szövegét...", label_visibility="collapsed")

    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
    analyze_clicked = st.button("Elemzés indítása", use_container_width=True)

    if analyze_clicked:
        if not api_key:
            st.error("Kérlek, add meg az Anthropic API kulcsodat a bal oldali sávban.")
            return
        if not law_text.strip() or not explanation_text.strip():
            st.error("Kérlek, töltsd ki mindkét szövegmezőt.")
            return

        user_prompt = f"""Annotáld az alábbi jogalkotói indokolás szövegét:

TÖRVÉNYSZÖVEG:
{law_text}

JOGALKOTÓI INDOKOLÁS:
{explanation_text}"""

        try:
            with st.spinner("Elemzés folyamatban..."):
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=8192,
                    temperature=0,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                annotated_text = response.content[0].text

            segments = parse_annotated_text(annotated_text)

            if not segments:
                st.warning("Az elemzés nem adott értékelhető eredményt. Próbáld újra.")
                with st.expander("Nyers válasz"):
                    st.code(annotated_text, language=None)
                return

            stats = compute_stats(segments)

            st.markdown('<div class="results-header">Eredmények</div>', unsafe_allow_html=True)
            render_metrics(stats)
            render_progress_bar(stats)

            st.markdown('<div class="section-header">Kategória bontás</div>', unsafe_allow_html=True)
            render_breakdown(stats)

            st.markdown('<div class="section-header">Annotált indokolás</div>', unsafe_allow_html=True)
            render_annotated_text(segments)

            st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
            with st.expander("Szegmensek listája"):
                st.markdown(render_segment_list(segments), unsafe_allow_html=True)

        except anthropic.AuthenticationError:
            st.error("Hibás API kulcs. Ellenőrizd a kulcsodat.")
        except anthropic.RateLimitError:
            st.error("API rate limit. Várj egy kicsit és próbáld újra.")
        except Exception as e:
            st.error(f"Hiba történt: {str(e)}")

    st.markdown('<div class="app-footer">&copy; 2026 dr. Kiss Rebeka</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
