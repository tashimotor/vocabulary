#!/usr/bin/env python3
"""
Генератор печатной вёрстки словарных карточек А6 (алгоритм — в SKILL.md рядом).

Скрипт делает только вёрстку (пагинация по ROWS-строкам, сетка 2 колонки, тайлинг
4 карточек на лист А4). Сортировку по алфавиту и выделение орфограммы <b> нужно
сделать заранее (это лингвистическая задача, не автоматизируется шаблоном) —
на вход подаётся уже готовый, уже отсортированный список.

Вход — JSON:
  {
    "title": "2 класс",
    "words": ["<b>а</b>лфавит", "<b>а</b>нте<b>нн</b>а", "б<b>е</b>рёза", ...]
  }

Использование:
  python3 generate_cards.py words.json --font 20 --cap 28 --out ../../../2-class-print.html

Размер шрифта (--font) и ёмкость карточки (--cap, слов на карточку, чётное число —
строк-в-колонке будет cap/2) подбираются рендером под конкретный список слов,
см. раздел "Единый размер шрифта" в SKILL.md. Дефолты — стартовая точка, не константы.
"""
import argparse
import json
import math
import sys


def paginate(words, cap):
    return [words[i:i + cap] for i in range(0, len(words), cap)]


def card_html(title, page_words, cap):
    rows = cap // 2  # ROWS: фиксированная ёмкость колонки, одна и та же на всех страницах книжки
    split = min(len(page_words), rows)
    col1, col2 = page_words[:split], page_words[split:]
    items = "\n".join(f'      <div class="word">{w}</div>' for w in col1)
    if col2:
        items += "\n\n" + "\n".join(f'      <div class="word">{w}</div>' for w in col2)
    return f'''  <div class="card">
    <h1>{title}</h1>
    <div class="words" style="grid-template-rows: repeat({rows}, 1fr);">
{items}
    </div>
  </div>'''


def empty_card_html():
    return '  <div class="card"></div>'


def build(title, words, font_pt, cap):
    pages = paginate(words, cap)

    if len(pages) <= 1:
        # весь список влезает в одну карточку — размножить на все 4 слота листа
        # (даёт 4 готовых копии для вырезания, п.6 алгоритма в SKILL.md)
        one = pages[0] if pages else []
        cards = [card_html(title, one, cap) for _ in range(4)]
    else:
        cards = [card_html(title, p, cap) for p in pages]
        while len(cards) % 4 != 0:
            cards.append(empty_card_html())  # книжка, не тираж — пустая рамка, без дублей

    sheets = []
    for i in range(0, len(cards), 4):
        sheets.append('<div class="sheet">\n' + "\n\n".join(cards[i:i + 4]) + '\n</div>')
    sheets_html = "\n\n".join(sheets)

    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ background:#fff; color:#000; }}
  body {{ font-family: "Times New Roman", Georgia, serif; }}

  @page {{ size: A4; margin: 0; }}

  .sheet {{
    width: 210mm;
    height: 297mm;
    display: grid;
    grid-template-columns: 105mm 105mm;
    grid-template-rows: 148mm 148mm;
    page-break-after: always;
  }}
  .sheet:last-child {{ page-break-after: auto; }}

  .card {{
    width: 105mm;
    height: 148mm;
    box-sizing: border-box;
    border: 0.35mm dashed #000;
    padding: 9mm 7mm;
    display: flex;
    flex-direction: column;
  }}

  .card h1 {{
    font-size: {font_pt}pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 3mm;
    letter-spacing: 0.3mm;
  }}

  .words {{
    flex: 1;
    display: grid;
    grid-auto-flow: column;
    grid-template-columns: 1fr 1fr;
    column-gap: 6mm;
  }}

  .word {{
    font-size: {font_pt}pt;
    line-height: 1;
    align-self: center;
    white-space: nowrap;
  }}

  b {{ font-weight: bold; }}

  @media screen {{
    body {{ background:#888; padding: 10mm 0; }}
    .sheet {{ margin: 0 auto 10mm; box-shadow: 0 0 4mm rgba(0,0,0,0.4); }}
  }}
</style>
</head>
<body>

{sheets_html}

</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser(
        description="Собрать печатную HTML-вёрстку словарных карточек А6 из JSON-списка слов."
    )
    ap.add_argument("words_json", help='JSON-файл: {"title": "...", "words": ["<b>а</b>лфавит", ...]}')
    ap.add_argument("--font", type=int, default=23, help="Размер шрифта в pt (подбирается рендером, см. SKILL.md)")
    ap.add_argument("--cap", type=int, default=28, help="Ёмкость карточки в словах (чётное число)")
    ap.add_argument("--out", required=True, help="Путь к выходному N-class-print.html")
    args = ap.parse_args()

    if args.cap % 2 != 0:
        sys.exit("--cap должен быть чётным (делится на 2 колонки)")

    with open(args.words_json, encoding="utf-8") as f:
        data = json.load(f)
    title = data["title"]
    words = data["words"]

    html = build(title, words, args.font, args.cap)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    pages = paginate(words, args.cap)
    sheets_count = 1 if len(pages) <= 1 else math.ceil(len(pages) / 4)
    print(f"слов: {len(words)}; карточек-страниц: {max(1, len(pages))}; листов А4: {sheets_count}")
    print(f"записано в {args.out}")


if __name__ == "__main__":
    main()
