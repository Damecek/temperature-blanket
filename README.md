# Temperature Blanket (Havlíčkův Brod)

Jednostránková aplikace pro vizualizaci „teplotní deky“ z denních maximálních teplot (TMA) stanice ČHMÚ **0-203-0-11656**.

## Produkce

Aplikace je publikovaná na:

- https://damecek.github.io/temperature-blanket/

## Co bylo opraveno

- 404 na `favicon.ico` je odstraněna přidáním explicitního favicon linku (SVG data URI).
- Aplikace už nenačítá data z externích URL v prohlížeči.
- Data se čtou pouze z lokálních JSON souborů v `data/chmi`.
- Aktualizace datasetů je řešená přes GitHub Action spuštěnou on-demand.
- Do repozitáře se ukládají normalizovaná data pouze pro element `TMA` (kvůli velikosti souborů i rychlosti načítání).
- Zdrojová strategie při aktualizaci:
  - historical: `historical_csv` endpoint pro `TMA`,
  - recent: `recent` JSON endpointy, filtrované na `TMA` (`/daily/{MM}/...` a fallback `/daily/dly-{WSI}-{YYYYMM}.json`).

## Aktualizace datasetů (on-demand)

Spusť workflow **Update CHMI Local Data** v GitHub Actions (`workflow_dispatch`):

1. volitelně zadej `year` (např. `2026`) pro recent datasety,
2. workflow stáhne:
   - `data/chmi/historical/dly-0-203-0-11656.json`,
   - `data/chmi/recent/<year>/dly-0-203-0-11656-<year><month>.json`,
   - `data/chmi/recent/<year>/index.json`,
3. při změně dat workflow commitne a pushne data přímo do `main`.

## Lokální aktualizace dat (bez Actions)

```bash
python3 scripts/update_chmi_local_data.py --year 2026 --station 0-203-0-11656 --out data/chmi
```

## Lokální spuštění

Stačí statický server nad root adresářem repozitáře:

```bash
python3 -m http.server 4173
```

Pak otevřít:

- http://localhost:4173/

## Struktura

- `index.html` – UI + logika načítání a vykreslení.
- `.github/workflows/update-chmi-data.yml` – on-demand aktualizace lokálních CHMI datasetů.
- `data/chmi/` – lokální JSON datasety používané stránkou.
- `AGENTS.md` – instrukce pro další úpravy repozitáře.
