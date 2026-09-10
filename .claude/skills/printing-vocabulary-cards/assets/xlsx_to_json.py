#!/usr/bin/env python3
"""
Конвертер xlsx -> каноничный JSON {"title", "words"} для printing-vocabulary-cards.

Читает список слов из xlsx, где орфограмма уже выделена ручным форматированием
"полужирный" на уровне отдельных букв внутри ячейки (rich text runs), и превращает
её в <b>...</b> — тот же формат, который принимает generate_cards.py и который
использует compare_orthograms.py для сверки с разметкой, сделанной AI по правилам
из SKILL.md ("Выделение орфограммы").

Не использует openpyxl (может быть не установлен) — xlsx это zip с XML,
разбирается напрямую через xml.etree + zipfile.

Использование:
  python3 xlsx_to_json.py words.xlsx --title "2 класс" --column A --out words.json

--column — буква колонки с словами (по умолчанию A, первая колонка листа).
--sheet  — номер листа (по умолчанию 1, т.е. xl/worksheets/sheet1.xml).
"""
import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def parse_shared_strings(zf):
    """index -> (plain_text, html_with_b)"""
    try:
        raw = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(raw)
    shared = []
    for si in root.findall("m:si", NS):
        runs = si.findall("m:r", NS)
        if runs:
            html_parts, plain_parts = [], []
            for r in runs:
                t = r.find("m:t", NS)
                text = t.text or "" if t is not None else ""
                plain_parts.append(text)
                rpr = r.find("m:rPr", NS)
                bold = rpr is not None and rpr.find("m:b", NS) is not None
                html_parts.append(f"<b>{text}</b>" if bold else text)
            shared.append(("".join(plain_parts), "".join(html_parts)))
        else:
            t = si.find("m:t", NS)
            text = t.text or "" if t is not None else ""
            shared.append((text, text))
    return shared


def col_letters(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return m.group(1), int(m.group(2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx_path")
    ap.add_argument("--title", required=True, help='Заголовок карточки, напр. "2 класс"')
    ap.add_argument("--column", default="A", help="Буква колонки со словами (по умолчанию A)")
    ap.add_argument("--sheet", type=int, default=1, help="Номер листа (по умолчанию 1)")
    ap.add_argument("--out", required=True, help="Путь к выходному JSON")
    args = ap.parse_args()

    with zipfile.ZipFile(args.xlsx_path) as zf:
        shared = parse_shared_strings(zf)
        sheet_xml = zf.read(f"xl/worksheets/sheet{args.sheet}.xml")

    root = ET.fromstring(sheet_xml)
    sheet_data = root.find("m:sheetData", NS)
    if sheet_data is None:
        sys.exit(f"Не нашёл sheetData на листе {args.sheet}")

    rows = []
    for row in sheet_data.findall("m:row", NS):
        for c in row.findall("m:c", NS):
            ref = c.get("r")
            col, rownum = col_letters(ref)
            if col != args.column:
                continue
            t = c.get("t")
            v = c.find("m:v", NS)
            if v is None or v.text is None:
                continue
            if t == "s":
                plain, html = shared[int(v.text)]
            else:
                plain = html = v.text
            if plain.strip():
                rows.append((rownum, html))

    rows.sort(key=lambda x: x[0])
    words = [html for _, html in rows]

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"title": args.title, "words": words}, f, ensure_ascii=False, indent=2)

    print(f"слов: {len(words)}; записано в {args.out}")


if __name__ == "__main__":
    main()
