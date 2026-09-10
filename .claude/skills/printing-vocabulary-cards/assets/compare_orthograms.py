#!/usr/bin/env python3
"""
Сверка разметки орфограмм между двумя каноничными JSON-списками слов
(формат {"title", "words": ["<b>а</b>лф<b>а</b>вит", ...]} — тот же, что ест
generate_cards.py и производит xlsx_to_json.py).

Сопоставляет слова по чистому тексту (без <b>), не по порядку — списки могут
быть отсортированы по-разному. Для каждого общего слова сравнивает, какие
именно буквы выделены жирным, и печатает только различающиеся слова.

Использование:
  python3 compare_orthograms.py mine.json reference.json
"""
import argparse
import json
import re


def plain(html):
    return re.sub(r"</?b>", "", html)


def bold_mask(html):
    mask = []
    i, bold = 0, False
    while i < len(html):
        if html[i:i + 3] == "<b>":
            bold, i = True, i + 3
        elif html[i:i + 4] == "</b>":
            bold, i = False, i + 4
        else:
            mask.append(bold)
            i += 1
    return mask


def index_by_plain(words):
    out = {}
    for w in words:
        out[plain(w)] = (w, bold_mask(w))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a_json", help="Свой список (напр. разметка AI)")
    ap.add_argument("b_json", help="Эталонный список (напр. из xlsx_to_json.py)")
    ap.add_argument("--a-label", default="A")
    ap.add_argument("--b-label", default="B")
    args = ap.parse_args()

    with open(args.a_json, encoding="utf-8") as f:
        a = json.load(f)["words"]
    with open(args.b_json, encoding="utf-8") as f:
        b = json.load(f)["words"]

    a_idx, b_idx = index_by_plain(a), index_by_plain(b)
    only_a = sorted(set(a_idx) - set(b_idx))
    only_b = sorted(set(b_idx) - set(a_idx))
    common = sorted(set(a_idx) & set(b_idx))

    if only_a:
        print(f"=== Есть только в {args.a_label} ===")
        for p in only_a:
            print(" ", p)
    if only_b:
        print(f"=== Есть только в {args.b_label} ===")
        for p in only_b:
            print(" ", p)

    diffs = [p for p in common if a_idx[p][1] != b_idx[p][1]]
    print(f"\n=== Различия в разметке жирным ({len(diffs)} из {len(common)} общих слов) ===")
    for p in diffs:
        ahtml, _ = a_idx[p]
        bhtml, _ = b_idx[p]
        print(f"{p}:")
        print(f"   {args.a_label}: {ahtml}")
        print(f"   {args.b_label}: {bhtml}")

    if not diffs and not only_a and not only_b:
        print("Полное совпадение.")


if __name__ == "__main__":
    main()
