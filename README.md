# Temperature Blanket (Havlíčkův Brod)

Jednostránková aplikace pro vizualizaci „teplotní deky“ z denních maximálních teplot (TMA) stanice ČHMÚ **0-203-0-11656**.

## Produkce

Aplikace je publikovaná na:

- https://damecek.github.io/temperature-blanket/

## Co bylo opraveno

- 404 na `favicon.ico` je odstraněna přidáním explicitního favicon linku (SVG data URI).
- Načítání dat řeší CORS fallback řetězem zdrojů:
  1. přímý ČHMÚ CSV endpoint,
  2. veřejný CORS proxy endpoint (`api.codetabs.com`),
  3. lokální snapshot CSV v repozitáři (`data/dly-0-203-0-11656-TMA.csv`).

Díky tomu stránka funguje i při CORS blokaci na GitHub Pages.

## Lokální spuštění

Stačí statický server nad root adresářem repozitáře:

```bash
python3 -m http.server 4173
```

Pak otevřít:

- http://localhost:4173/

## Struktura

- `index.html` – UI + logika načítání a vykreslení.
- `data/dly-0-203-0-11656-TMA.csv` – lokální fallback dataset.
- `AGENTS.md` – instrukce pro další úpravy repozitáře.
