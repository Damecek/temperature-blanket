#!/usr/bin/env python3
import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


TARGET_ELEMENT = "TMA"


def clean_token(value):
    return str(value or "").strip().strip('"')


def safe_json_parse(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def extract_daily_list(parsed):
    if isinstance(parsed, list):
        return parsed
    if not isinstance(parsed, dict):
        return []
    for key in ("data", "rows", "items", "result", "observations", "values"):
        value = parsed.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = extract_daily_list(value)
            if nested:
                return nested
        if isinstance(value, str) and value.strip():
            nested_parsed = safe_json_parse(value)
            if nested_parsed is not None:
                nested = extract_daily_list(nested_parsed)
                if nested:
                    return nested
    nested = parsed.get("contents") or parsed.get("body") or parsed.get("payload")
    if isinstance(nested, str) and nested.strip():
        nested_parsed = safe_json_parse(nested)
        return extract_daily_list(nested_parsed)
    return []


def parse_tuple_item(item):
    parts = [clean_token(x) for x in item]
    element = next((part for part in parts if re.fullmatch(r"[A-Z]{3}", part or "")), None)
    if element and element != TARGET_ELEMENT:
        return None

    date_index = next(
        (
            idx
            for idx, part in enumerate(parts)
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", part or "")
            or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", part or "")
        ),
        -1,
    )
    if date_index < 0:
        return None

    date_raw = parts[date_index]
    date_value = date_raw[:10] if len(date_raw) >= 10 else date_raw
    temp = None
    for token in parts[date_index + 1 :]:
        try:
            temp = float(token)
            break
        except Exception:
            continue

    if temp is None:
        return None
    return {"date": date_value, "TMA": temp}


def split_tuple(raw):
    return [p for p in re.split(r"[,;|\t]", raw) if p.strip()]


def parse_tuple_json(text):
    rows = []
    for match in re.finditer(r"\{([^{}]+)\}", text):
        row = parse_tuple_item(split_tuple(match.group(1)))
        if row:
            rows.append(row)
    if rows:
        return rows

    for match in re.finditer(r"\[([^[\]]+)\]", text):
        row = parse_tuple_item(split_tuple(match.group(1)))
        if row:
            rows.append(row)
    return rows


def parse_json_lines(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{") or not line.endswith("}"):
            continue
        parsed = safe_json_parse(line)
        if not isinstance(parsed, dict):
            continue
        rows.extend(parse_daily_json(json.dumps(parsed)))
    return rows


def parse_daily_json(text):
    parsed = safe_json_parse(text)
    if parsed is not None:
        items = extract_daily_list(parsed)
        rows = []
        for item in items:
            if isinstance(item, list):
                row = parse_tuple_item(item)
                if row:
                    rows.append(row)
                continue

            if not isinstance(item, dict):
                continue

            element = item.get("element") or item.get("ELEMENT") or item.get("el") or item.get("prvek") or item.get("code") or item.get("elementCode")
            if element and clean_token(element).upper() != TARGET_ELEMENT:
                continue

            date_value = item.get("date") or item.get("dt") or item.get("datum") or item.get("DATE") or item.get("d")
            temp_raw = item.get("TMA")
            if temp_raw is None:
                temp_raw = item.get("value")
            if temp_raw is None:
                temp_raw = item.get("tma")
            if temp_raw is None and isinstance(item.get("elements"), dict):
                temp_raw = item["elements"].get("TMA")
            if temp_raw is None:
                temp_raw = item.get("v")

            if not date_value:
                continue
            try:
                temp = float(temp_raw)
            except Exception:
                continue
            rows.append({"date": str(date_value), "TMA": temp})
        if rows:
            return rows

    tuple_rows = parse_tuple_json(text)
    if tuple_rows:
        return tuple_rows
    return parse_json_lines(text)


def dedupe_rows(rows):
    by_date = {}
    for row in rows:
        date_value = row.get("date")
        tma = row.get("TMA")
        if not isinstance(date_value, str):
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
            continue
        if not isinstance(tma, (int, float)):
            continue
        by_date[date_value] = {"date": date_value, "TMA": float(tma)}
    return [by_date[k] for k in sorted(by_date.keys())]


def parse_csv_rows(text):
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return []
    rows = []
    reader = csv.DictReader(lines)
    for rec in reader:
        element = clean_token(rec.get("ELEMENT") or rec.get("element")).upper()
        if element and element != TARGET_ELEMENT:
            continue
        dt_raw = clean_token(rec.get("DT") or rec.get("DATE") or rec.get("date"))
        date_value = dt_raw[:10] if len(dt_raw) >= 10 else dt_raw
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
            continue
        try:
            temp = float(clean_token(rec.get("VALUE") or rec.get("value")))
        except Exception:
            continue
        rows.append({"date": date_value, "TMA": temp})
    return rows


def fetch_text(url):
    try:
        with urlopen(url, timeout=120) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        result = subprocess.run(
            ["curl", "--fail", "--silent", "--show-error", "--location", "--max-time", "120", url],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout


def fetch_optional_text(url):
    try:
        return fetch_text(url)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--station", default="0-203-0-11656")
    parser.add_argument("--year", required=True)
    parser.add_argument("--out", default="data/chmi")
    args = parser.parse_args()

    if not re.fullmatch(r"\d{4}", args.year):
        print(f"Neplatný rok: {args.year}", file=sys.stderr)
        return 1

    out_base = Path(args.out)
    hist_dir = out_base / "historical"
    recent_dir = out_base / "recent" / args.year
    hist_dir.mkdir(parents=True, exist_ok=True)
    recent_dir.mkdir(parents=True, exist_ok=True)

    station = args.station

    hist_url = (
        "https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/temperature/"
        f"dly-{station}-{TARGET_ELEMENT}.csv"
    )
    hist_text = fetch_text(hist_url)
    hist_rows = dedupe_rows(parse_csv_rows(hist_text))
    if not hist_rows:
        print("Historický dataset je prázdný po filtraci na TMA.", file=sys.stderr)
        return 1
    hist_out = hist_dir / f"dly-{station}.json"
    hist_out.write_text(json.dumps(hist_rows, ensure_ascii=False), encoding="utf-8")

    for old in recent_dir.glob(f"dly-{station}-{args.year}*.json"):
        old.unlink()

    months = []
    for month in range(1, 13):
        mm = f"{month:02d}"
        recent_url = (
            "https://opendata.chmi.cz/meteorology/climate/recent/data/daily/"
            f"{mm}/dly-{station}-{args.year}{mm}.json"
        )
        text = fetch_optional_text(recent_url)
        if text is None:
            continue
        rows = dedupe_rows(parse_daily_json(text))
        if not rows:
            continue
        out_file = recent_dir / f"dly-{station}-{args.year}{mm}.json"
        out_file.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        months.append(mm)

    index_file = recent_dir / "index.json"
    index_file.write_text(
        json.dumps({"station": station, "year": int(args.year), "months": months}, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Updated station={station} year={args.year} months={','.join(months)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
