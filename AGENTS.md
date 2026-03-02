# AGENTS.md

## Scope
Tyto instrukce platí pro celý repozitář.

## Cíl projektu
- Udržovat jednoduchou statickou stránku pro GitHub Pages: https://damecek.github.io/temperature-blanket/
- Minimalizovat závislosti (ideálně bez build kroku).

## Pravidla pro změny
- Preferuj úpravy přímo v `index.html`, pokud není silný důvod dělit soubory.
- Při práci s externími daty počítej s CORS omezeními na GitHub Pages a vždy zachovej funkční fallback.
- Zachovej české texty v UI i dokumentaci.

## Poznatky k CHMI datasetům (Klimatologicka_data_popis.pdf)
- Zdroj: https://opendata.chmi.cz/meteorology/climate/Klimatologicka_data_popis.pdf
- `historical` JSON denní data jsou po stanici: `.../historical/data/daily/dly-{WSI}.json` (obsahuje více prvků, ne jen TMA).
- `recent` JSON denní data jsou měsíční po stanici: `.../recent/data/daily/{MM}/dly-{WSI}-{YYYYMM}.json` (obsahuje více prvků, ne jen TMA).
- Samostatný endpoint pouze pro jeden prvek (např. `TMA`) je podle PDF k dispozici u `historical_csv`: `.../historical_csv/data/daily/temperature/dly-{WSI}-{PRVEK}.csv`.
- Pro aktuální rok (`recent`) není v PDF uvedena analogická denní cesta „jen TMA“; je nutná filtrace na `TMA` při zpracování dat.
- Praktické pravidlo pro tento projekt: ukládat do repozitáře normalizované lokální JSON soubory už filtrované na `TMA`, aby byly malé a stabilní pro GitHub Pages.
- Preferovaná implementace updateru: historical brát z `historical_csv` TMA endpointu; recent brát z `recent` JSON a filtrovat na `TMA`.

## Ověření před commitem
- Otestuj lokálně přes statický server (`python3 -m http.server`).
- Zkontroluj, že se stránka načte bez chyb v konzoli kvůli chybějícím assetům (např. favicon).
- Pokud je to vizuální změna, pořiď screenshot.

## Release a update dat přes `gh`
- Cíl: změny v kódu poslat do `main` a pak ručně spustit workflow **Update CHMI Local Data**.
- Doporučený postup:
  1. `git status --short`
  2. `git add <soubory>`
  3. `git commit -m "..."` (anglicky, stručně)
  4. `git push origin main`
  5. `gh workflow run "Update CHMI Local Data" --ref main -f year=$(date +%Y)`
  6. `gh run list --workflow "Update CHMI Local Data" --limit 1`
  7. `gh run watch`
- Poznámky:
  - Pokud je potřeba konkrétní rok, nahraď `year=$(date +%Y)` explicitně (např. `-f year=2026`).
  - Workflow po stažení dat samo commitne změny v `data/chmi` přímo do `main`, pokud jsou rozdíly.
