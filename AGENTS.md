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

## Ověření před commitem
- Otestuj lokálně přes statický server (`python3 -m http.server`).
- Zkontroluj, že se stránka načte bez chyb v konzoli kvůli chybějícím assetům (např. favicon).
- Pokud je to vizuální změna, pořiď screenshot.
