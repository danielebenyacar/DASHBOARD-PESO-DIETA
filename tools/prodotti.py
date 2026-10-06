# Crea il database dei prodotti italiani per la ricerca nei Pasti, dall'export di Open Food Facts.
# Uso (solo libreria standard di Python):
#   curl -sL https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz | gunzip \
#     | python3 tools/prodotti.py beta/prodotti-it-AAAA-MM-GG.txt
# Poi aggiorna DB_URL in index.html, la versione in sw.js e il footer.
# Dati: Open Food Facts contributors, licenza ODbL 1.0 (il file prodotto resta sotto ODbL).
import sys, csv, re, datetime

MAX = int(sys.argv[2]) if len(sys.argv) > 2 else 0   # 0 = tutti

def num(s):
    try:
        v = float(str(s).replace(",", "."))
        return v if v == v and abs(v) != float("inf") else None
    except ValueError:
        return None

def fmt(v):
    v = round(v, 1)
    return str(int(v)) if v == int(v) else str(v)

def clean(s, n):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s[:n].rstrip()

def it_rank(tags):
    # Popolarita' in Italia dai tag di Open Food Facts: "top-100-it-scans-2024" = tra i 100 piu' scansionati in Italia.
    best = None
    for t in tags.split(","):
        m = re.match(r"top-(\d+)-it-scans-\d{4}$", t)
        v = int(m.group(1)) if m else 10 ** 6 if re.match(r"at-least-\d+-it-scans-\d{4}$", t) else 10 ** 7 if re.match(r"top-country-it-scans-\d{4}$", t) else None
        if v is not None and (best is None or v < best):
            best = v
    return best

def main(out_path):
    csv.field_size_limit(1 << 30)
    r = csv.reader(open(sys.stdin.fileno(), encoding="utf-8", errors="replace", newline=""), delimiter="\t", quoting=csv.QUOTE_NONE)
    head = next(r); ix = {h: i for i, h in enumerate(head)}
    get = lambda row, k: row[ix[k]] if k in ix and ix[k] < len(row) else ""
    ci = ix.get("countries_tags")
    best = {}
    for row in r:
        if ci is not None and (len(row) <= ci or "en:italy" not in row[ci]):
            continue
        code = get(row, "code").strip()
        name = clean(get(row, "product_name"), 70)
        if not code or not code.isdigit() or len(name) < 2 or re.search(r"[\u0370-\u03ff\u0400-\u04ff\u0590-\u06ff\u0e00-\u0e7f\u3040-\u9fff\uac00-\ud7af]", name):
            continue   # niente nomi in alfabeti non latini (greco, cirillico, arabo, asiatici...)
        k = num(get(row, "energy-kcal_100g"))
        if k is None:
            kj = num(get(row, "energy-kj_100g"))
            if kj is None:
                kj = num(get(row, "energy_100g"))
            k = kj / 4.184 if kj is not None else None
        p, c, g = (num(get(row, x)) for x in ("proteins_100g", "carbohydrates_100g", "fat_100g"))
        if k is None or p is None or c is None or g is None:
            continue
        if not (0 <= k <= 900 and 0 <= p <= 100 and 0 <= c <= 100 and 0 <= g <= 100 and p + c + g <= 105):
            continue
        est = 4 * p + 4 * c + 9 * g          # valori incoerenti (es. kJ scritti come kcal) = scartati
        if not (0.6 * k - 20 <= est <= 1.3 * k + 20):
            continue
        brand = clean(get(row, "brands").split(",")[0], 40)
        sq, pq = num(get(row, "serving_quantity")), num(get(row, "product_quantity"))
        sq = sq if sq is not None and 0 < sq < 2000 else None
        pq = pq if pq is not None and 0 < pq < 3000 else None
        rank = it_rank(get(row, "popularity_tags"))
        italian = len(code) == 13 and "800" <= code[:3] <= "839"   # codice a barre italiano
        if rank is None and not italian:   # mai scansionato in Italia e non italiano: quasi sempre un prodotto estero
            continue
        scans = num(get(row, "unique_scans_n")) or 0
        comp = num(get(row, "completeness")) or 0
        rec = (rank if rank is not None else 10 ** 8, -scans, -comp, code, name, brand, k, p, c, g, sq, pq)
        key = (name.lower(), brand.lower())
        if key not in best or rec[:3] < best[key][:3]:   # stesso nome e marca: tiene il piu' popolare
            best[key] = rec
    recs = sorted(best.values(), key=lambda x: (x[0], x[1], x[2], x[4].lower()))
    if MAX:
        recs = recs[:MAX]
    seen = set()
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("#prodotti-it\t%s\tOpen Food Facts contributors, ODbL 1.0 https://opendatacommons.org/licenses/odbl/1-0/\t%d\n" % (datetime.date.today().isoformat(), len(recs)))
        for rank, scans, comp, code, name, brand, k, p, c, g, sq, pq in recs:
            if code in seen:
                continue
            seen.add(code)
            f.write("\t".join([code, name, brand, str(round(k)), fmt(p), fmt(c), fmt(g), fmt(sq) if sq else "", fmt(pq) if pq else ""]) + "\n")
    print("prodotti:", len(seen), file=sys.stderr)

if __name__ == "__main__":
    main(sys.argv[1])
