import csv, os, requests

os.makedirs("input_louvre", exist_ok=True)

with open("results_filter_china_louvre.csv", newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, delimiter=';'):
        ark = row["ARK"]
        r = requests.get(f"https://collections.louvre.fr/ark:/53355/{ark}.json")
        if r.ok:
            with open(f"input_louvre/{ark}.json", "w", encoding="utf-8") as out:
                out.write(r.text)
