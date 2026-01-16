# HAE Elemző

Törvény indokolás hozzáadott érték vizsgálat — Streamlit alkalmazás Claude Opus 4.5 API-val.

## Fájlstruktúra

```
hae_analyzer_app/
├── app.py                      # Fő alkalmazás
├── requirements.txt            # Függőségek
├── .gitignore                  # Git ignore szabályok
├── .streamlit/
│   └── secrets.toml.example    # Secrets minta (NE commitold a valódit!)
└── README.md                   # Ez a fájl
```

---

## 1. GitHub Repository létrehozása

### 1.1 Új repo létrehozása

1. Menj a https://github.com/new oldalra
2. Repository name: `hae-analyzer` (vagy amit szeretnél)
3. Visibility: **Private** (ha nem akarod publikussá tenni)
4. NE pipáld be az "Add a README" opciót
5. Kattints: **Create repository**

### 1.2 Fájlok feltöltése

**Opció A - GitHub webes felület:**
1. A repo oldalán kattints: **uploading an existing file**
2. Húzd be az összes fájlt (app.py, requirements.txt, .gitignore, .streamlit mappa)
3. Commit message: "Initial commit"
4. Kattints: **Commit changes**

**Opció B - Git parancssorból:**
```bash
cd hae_analyzer_app

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/FELHASZNALO/hae-analyzer.git
git push -u origin main
```

### 1.3 FONTOS: API kulcs védelme

**SOHA ne commitold az API kulcsodat!**

A `.gitignore` már tartalmazza:
```
.streamlit/secrets.toml
```

---

## 2. Streamlit Cloud Deploy

### 2.1 Streamlit Cloud regisztráció

1. Menj a https://share.streamlit.io/ oldalra
2. Kattints: **Sign in with GitHub**
3. Engedélyezd a GitHub hozzáférést

### 2.2 Új app létrehozása

1. Kattints: **New app**
2. Töltsd ki:
   - **Repository**: válaszd ki a `hae-analyzer` repót
   - **Branch**: `main`
   - **Main file path**: `app.py`
3. Kattints: **Advanced settings**

### 2.3 Secrets beállítása (API kulcs)

A **Advanced settings** ablakban:

1. Kattints a **Secrets** fülre
2. Másold be:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-XXXXXXXXXXXXXXXX"
```
3. Cseréld ki a valódi API kulcsodra

**Vagy** később a Settings-ben:
1. App deploy után menj a **Settings** (fogaskerék ikon)
2. Bal oldalt: **Secrets**
3. Add meg ugyanezt a formátumot

### 2.4 Deploy

1. Kattints: **Deploy!**
2. Várj 1-2 percet amíg felépül
3. Kapsz egy URL-t: `https://APPNEV.streamlit.app`

---

## 3. Lokális futtatás (fejlesztéshez)

### 3.1 Környezet beállítása

```bash
# Virtuális környezet (ajánlott)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# VAGY: venv\Scripts\activate  # Windows

# Függőségek
pip install -r requirements.txt
```

### 3.2 Secrets beállítása lokálisan

```bash
# Hozd létre a secrets fájlt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Szerkeszd és add meg a valódi API kulcsodat
nano .streamlit/secrets.toml
```

Tartalom:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-XXXXXXXXXXXXXXXX"
```

### 3.3 Futtatás

```bash
streamlit run app.py
```

Megnyílik: http://localhost:8501

---

## 4. API kulcs beszerzése

1. Menj: https://console.anthropic.com/
2. Regisztrálj / jelentkezz be
3. **API Keys** menü
4. **Create Key**
5. Másold ki a kulcsot (csak egyszer látod!)

---

## Kategóriák

### HAE - Hozzáadott Érték

| Kód | Kategória | Szín |
|-----|-----------|------|
| 1 | Célmeghatározás | Piros |
| 2 | Belső utalás | Szürke |
| 3 | Külső jogforrás hivatkozás | Kék |
| 4 | Bírósági joggyakorlat és AB határozatok | Sötétzöld |
| 5 | Szakirodalom / Kutatási eredmény | Barna |
| 6 | Összevetés korábbi szabályozással | Zöld |
| 7 | Hatásvizsgálat | Narancssárga |
| 8 | Egyéb magyarázat és példák | Sárga |

### NEM - Nem Hozzáadott Érték

| Kód | Kategória | Szín |
|-----|-----------|------|
| 1 | Szó szerinti átmásolás | Lila |
| 2 | Átfogalmazás | Sötétkék |
| 3 | Kivonatolás | Világosszürke |
| 4 | Hibás indokolás | Fekete |

---

## Minőségi besorolás

- **Jó**: HAE >= 60%
- **Közepes**: HAE 30-60%
- **Gyenge**: HAE < 30%

---

## Technikai részletek

- **Model**: Claude Opus 4.5 (`claude-opus-4-5-20251101`)
- **Max tokens**: 8192
- **Framework**: Streamlit

---

## Hibaelhárítás

**"Hibás API kulcs"**
- Ellenőrizd, hogy a teljes kulcsot másoltad-e be
- A kulcs `sk-ant-api03-` kezdetű

**"API rate limit"**
- Várj 1-2 percet és próbáld újra
- Ellenőrizd az Anthropic Console-ban a limitedet

**Streamlit Cloud nem látja a repót**
- Ellenőrizd, hogy a repo neve helyes
- Ellenőrizd, hogy engedélyezted-e a Streamlit GitHub hozzáférését

---

## Licenc

MIT
