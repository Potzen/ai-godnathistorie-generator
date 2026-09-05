"""Bygger den kompakte danske frekvenstabel, som word_service bruger.

Køres kun under udvikling, ikke i produktion. Formålet er at undgå at have
'wordfreq' med som runtime-afhængighed: pakken fylder 58 MB, mens tabellen
her fylder under en halv megabyte og indeholder præcis det, vi skal bruge.

    pip install wordfreq
    python scripts/build_word_frequency.py

Resultatet skrives til services/data/da_ordfrekvens.json og versionsstyres.
"""
import json
import os
import sys

# Zipf-skalaen er logaritmisk: 5 = meget almindeligt ord, 3 = mindre
# almindeligt. Snittene her er valgt, så båndene får brugbare størrelser
# for dansk (se fordelingen i docstring nederst).
BAAND_GRAENSER = [
    (5.0, 1),   # meget almindeligt - 'og', 'er', 'bil'
    (4.3, 2),   # almindeligt       - 'kat', 'skov', 'kage'
    (3.6, 3),   # kendt             - 'trold', 'kollektivt'
    (0.0, 4),   # sjældnere         - resten af listen
]
# Ord der slet ikke er i listen får bånd 5 (svært/ukendt) i word_service.

ANTAL_ORD = 40000


def main():
    try:
        from wordfreq import top_n_list, zipf_frequency
    except ImportError:
        sys.exit("Kræver 'wordfreq'. Kør: pip install wordfreq")

    baand = {1: [], 2: [], 3: [], 4: []}
    for ord_ in top_n_list('da', ANTAL_ORD):
        # Spring tal, tegnsætning og etbogstavs-fragmenter over.
        if not ord_.isalpha() or len(ord_) < 2:
            continue
        z = zipf_frequency(ord_, 'da')
        for graense, b in BAAND_GRAENSER:
            if z >= graense:
                baand[b].append(ord_)
                break

    ud = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'services', 'data', 'da_ordfrekvens.json')
    os.makedirs(os.path.dirname(ud), exist_ok=True)
    with open(ud, 'w', encoding='utf-8') as fh:
        json.dump({str(k): v for k, v in baand.items()}, fh, ensure_ascii=False, separators=(',', ':'))

    ialt = sum(len(v) for v in baand.values())
    print(f"Skrev {ialt} ord til {ud} ({os.path.getsize(ud)/1024:.0f} KB)")
    for b in sorted(baand):
        print(f"  bånd {b}: {len(baand[b]):6} ord")


if __name__ == '__main__':
    main()
