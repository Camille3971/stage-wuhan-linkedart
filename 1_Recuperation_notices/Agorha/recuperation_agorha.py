
import csv, os, requests

os.makedirs("input_agorha", exist_ok=True)

with open("results_filter_china_agorha.csv", newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, delimiter=';'):
        uuid = row["uuid"]
        r = requests.get(f"https://agorha.inha.fr/ark:/54721/{uuid}.jsonld")
        if r.ok:
            with open(f"input_agorha/{uuid}.jsonld", "w", encoding="utf-8") as out:
                out.write(r.text)
