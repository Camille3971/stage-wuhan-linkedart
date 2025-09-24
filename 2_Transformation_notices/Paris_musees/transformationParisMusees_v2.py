import os
import re
import json
import requests
import sys

from urllib.parse import urlencode
from SPARQLWrapper import SPARQLWrapper, JSON

NOT_SPECIFIED_URI = 'http://example.org/not_specified'
NOT_FOUND_URI = 'http://example.org/not_found'

def get_wikidata_uri(label):
    endpoint_url = "https://query.wikidata.org/sparql"

    def run_query(search_label):
        query = f"""
        SELECT ?item WHERE {{
            SERVICE wikibase:mwapi {{
                bd:serviceParam wikibase:endpoint "www.wikidata.org";
                                wikibase:api "EntitySearch";
                                mwapi:search "{search_label.strip()}";
                                mwapi:language "fr".
                ?item wikibase:apiOutputItem mwapi:item.
            }}
        }} LIMIT 1
        """
        user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
        sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)

        try:
            results = sparql.query().convert()
            bindings = results["results"]["bindings"]
            if bindings:
                return bindings[0]["item"]["value"]
        except Exception as e:
            print(f"SPARQL error: {e}")
        return None

    # Essayer d’abord l’étiquette complète
    result = run_query(label)
    if result:
        return result

    for part in label.split(','):
        result = run_query(part)
        if result:
            return result

    return None

def get_getty_uri_from_label(label, special_cases=None):
    if not label:
        return None

    label_clean = label.strip().lower()

    # Gestion des cas particuliers
    if special_cases:
        for key, uri in special_cases.items():
            if key.strip().lower() in label_clean:
                return uri

    # Requête SPARQL plus souple
    query = f"""
    PREFIX skos: <https://www.w3.org/2004/02/skos/core#>
    SELECT DISTINCT ?subj WHERE {{
        ?subj skos:prefLabel ?lab .
        FILTER(LCASE(STR(?lab)) = "{label_clean}")
    }} LIMIT 1
    """
    params = {
        "query": query,
        "format": "application/sparql-results+json"
    }
    url = f"https://vocab.getty.edu/sparql?{urlencode(params)}"

    try:
        response = requests.get(url, headers={"Accept": "application/sparql-results+json"})
        response.raise_for_status()
        results = response.json().get("results", {}).get("bindings", [])
        return results[0]["subj"]["value"] if results else None
    except Exception as e:
        # Logique Wikidata ici
        try:
            return get_wikidata_uri(label_clean)
        except Exception as e1:
            print(f"Erreur lors de la récupération des données pour '{label}': {e1}")
            return None

def get_material_uri(label):
    cases = {"bronze":"https://vocab.getty.edu/aat/300010957","céramique":"https://vocab.getty.edu/aat/300235507","porcelaine":"https://vocab.getty.edu/aat/300010662","laque":"https://vocab.getty.edu/aat/300014916","bois":"https://vocab.getty.edu/aat/300011915","jade":"https://vocab.getty.edu/aat/300011119","grès":"https://vocab.getty.edu/aat/300011383","crin":"https://vocab.getty.edu/aat/300011819","soie":"https://vocab.getty.edu/aat/300014072","paillette":"https://vocab.getty.edu/aat/300014655","ecaille":"https://vocab.getty.edu/aat/300425558","métal":"https://vocab.getty.edu/aat/300010900","nacre":"https://vocab.getty.edu/aat/300011835","ivoire":"https://vocab.getty.edu/aat/300011857","argent":"https://vocab.getty.edu/aat/300011029","papier":"https://vocab.getty.edu/aat/300014110","gouache":"https://vocab.getty.edu/aat/300070114","velours":"https://vocab.getty.edu/aat/300014080","feuille d'or":"https://vocab.getty.edu/aat/300264831"}
    label_clean = label.strip().lower()
    for key, uri in cases.items():
        clean_key = key.strip().lower()
        if clean_key in label_clean:
            return uri
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def get_current_location_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"Cernuschi":"https://www.wikidata.org/wiki/Q1667022","Petit Palais":"https://vocab.getty.edu/ulan/500310009","Cognacq-Jay":"https://vocab.getty.edu/ulan/500309999","Galliera":"https://www.wikidata.org/wiki/Q1632912","Carnavalet":"https://vocab.getty.edu/ulan/500214785"})
    if result:
        return result
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def get_donateur_uri(label):
    result = get_getty_uri_from_label(label)
    if result:
        return result
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def get_carried_out_by_uri(label):
    result = get_getty_uri_from_label(label)
    if result:
        return result
    if label:
        return NOT_FOUND_URI
    return label

def conversion_parismusees_to_linkedart(data):
    result = {
        "@context": "https://linked.art/ns/v1/linked-art.json",
        "id": data.get("absolutePath"),
        "type": "HumanMadeObject",
        "_label": data.get("title"),
    
        # Informations générales sur l'oeuvre
        # "identified_by" : Titre, numéro d'inventaire et typologie de l'oeuvre
        "identified_by": [
            {
                "type": "Name",
                "classified_as": [
                    {
                        "id": "https://vocab.getty.edu/aat/300133025",
                        "type": "Type",
                        "_label": "Artwork"
                    },
                    {
                        "id": "https://vocab.getty.edu/aat/300404670",
                        "type": "Type",
                        "_label": "Primary Name"
                    }
                ],
                "content": data.get("title"),
                "language": [
                    {
                        "id": "https://vocab.getty.edu/page/aat/300388306",
                        "type": "Language",
                        "_label": "French",
                        "notation": "fr"
                    }
                ]
            },
            {
                "type": "Identifier",
                "classified_as": [
                    {
                        "id": "https://vocab.getty.edu/aat/300312355",
                        "type": "Type",
                        "_label": "Accession Number"
                    }
                ],
                "content": data.get("fieldOeuvreNumInventaire") if data.get("fieldOeuvreNumInventaire") else None
            }
        ],

        # "produced_by" : Date, lieu de création et auteur
        "produced_by": [
            {
                "type": "Production",
                "timespan": {
                "type": "TimeSpan",
                "_label": data.get("fieldOeuvreSiecle", {}).get("entity", {}).get("entityLabel") if isinstance(data.get("fieldOeuvreSiecle"), dict) else None,
                "begin_of_the_begin": str(data.get("fieldDateProduction", {}).get("startYear")) if isinstance(data.get("fieldDateProduction"), dict) else None,
                "end_of_the_end": str(data.get("fieldDateProduction", {}).get("endYear")) if isinstance(data.get("fieldDateProduction"), dict) else None
            },
               "took_place_at": [
                   {
                      "id": "https://vocab.getty.edu/tgn/1000111",
                      "type": "Place",
                     "_label": "Chine"
                 }
               ],
                "carried_out_by": [
                    {
                        "id": get_carried_out_by_uri(data.get("fieldAuteurAuteur")["entity"]["entityLabel"] if data.get("fieldAuteurAuteur") and len(
                            data["fieldAuteurAuteur"]) > 0 else NOT_SPECIFIED_URI),
                        "_label": data.get("fieldAuteurAuteur")["entity"]["entityLabel"] if data.get("fieldAuteurAuteur") and len(
                            data["fieldAuteurAuteur"]) > 0 else "Not Specified"
                    }
                ] if data.get("fieldAuteurAuteur") else []
            }
        ],
    
     # Informations physiques sur l'oeuvre
        # "made_of" : Matériaux
        "made_of": [
    {
        "id": get_material_uri(entity.get("entityLabel")),
        "type": "Material",
        "_label": entity.get("entityLabel")
    }
    for entity in data.get("queryFieldMateriauxTechnique", {}).get("entities", [])
    if entity.get("entityLabel")
] if data.get("queryFieldMateriauxTechnique") else 
[{
    "id": NOT_SPECIFIED_URI,
    "_label": "Not Specified"
}],
# "dimension" : dimensions longueur, hauteur, largeur
        "dimension": [
            {
                "type": "Dimension",
                "classified_as": [{"id": "https://vocab.getty.edu/aat/300055647", "type": "Type", "_label": "Width"}],
                "value": data.get("fieldOeuvreDimensions")[1]["entity"]["fieldDimensionValeur"]  if data.get("fieldOeuvreDimensions") and len(
                    data["fieldOeuvreDimensions"]) > 1 else None,
                "unit": {"id": "https://vocab.getty.edu/aat/300379098", "type": "MeasurementUnit",
                         "_label": "centimeters"}
            },
            {
                "type": "Dimension",
                "classified_as": [{"id": "https://vocab.getty.edu/aat/300055644", "type": "Type", "_label": "Height"}],
                "value": data.get("fieldOeuvreDimensions")[0]["entity"]["fieldDimensionValeur"] if data.get("fieldOeuvreDimensions") and len(
                    data["fieldOeuvreDimensions"]) > 0 else None,
                "unit": {"id": "https://vocab.getty.edu/aat/300379098", "type": "MeasurementUnit",
                         "_label": "centimeters"}
            },
            {
                "type": "Dimension",
                "classified_as": [{"id": "https://vocab.getty.edu/aat/300072633", "type": "Type", "_label": "depth"}],
                "value": data.get("fieldOeuvreDimensions")[2]["entity"]["fieldDimensionValeur"] if data.get("fieldOeuvreDimensions") and len(
                    data["fieldOeuvreDimensions"]) > 2 else None,
                "unit": {"id": "https://vocab.getty.edu/aat/300379098", "type": "MeasurementUnit",
                         "_label": "centimeters"}
            }
        ],
        # "referred_to_by" : commentaire
        "referred_to_by": [
            {
                "type": "LinguisticObject",
                "classified_as": [
                    {
                        "id": "https://vocab.getty.edu/aat/300435416",
                        "type": "Type",
                        "_label": "Description",
                        "classified_as": [
                            {
                                "id": "https://vocab.getty.edu/aat/300418049",
                                "type": "Type",
                                "_label": "Brief Text"
                            }
                        ]
                    }
                ],
                "content": data.get("fieldOeuvreDescriptionIcono")["value"] if data.get("fieldOeuvreDescriptionIcono") else None
            }
        ],

        # Informations sur l'état juridique de l'oeuvre
        # "current_location" : Emplacement actuel
        "current_location": [
            {
                "id": get_current_location_uri(data.get("queryFieldMusee")["entities"][0]["entityLabel"]),
                "type": "Place",
                "_label": data.get("queryFieldMusee")["entities"][0]["entityLabel"]
            }
        ],

    }

    changed_ownership_through = [
    {
        "type": "Acquisition",
        "_label": data.get("queryFieldModaliteAcquisition", {}).get("entities", [{}])[0].get("entityLabel", "No Ownership Transfer"),
        "transferred_title_from": [
            {
                "id": get_donateur_uri(data.get("queryFieldDonateurs", {}).get("entities", [{}])[0].get("entityLabel", NOT_SPECIFIED_URI)),
                "_label": data.get("queryFieldDonateurs", {}).get("entities", [{}])[0].get("entityLabel", "Not Specified")
            }
        ] if data.get("queryFieldDonateurs") else []
    }
]

    if len(data.get("queryFieldModaliteAcquisition", {}).get("entities", [])) > 0:
        result["changed_ownership_through"] = changed_ownership_through

    
    return result

# Lancement de la transformation 
input_dir = "input_parismusees"
output_dir = "output_parismusees"
os.makedirs(output_dir, exist_ok=True)

# Lecture du dossier source
for f in os.listdir(input_dir):
    if f.endswith(".json"):
        with open(os.path.join(input_dir, f), "r", encoding="utf-8") as infile:
            data = json.load(infile)

        # Conversion
        result = conversion_parismusees_to_linkedart(data)

        # Ecriture des fichiers Linked Art
        with open(os.path.join(output_dir, f.replace(".json", "_linkedart.jsonld")), "w", encoding="utf-8") as outfile:
            json.dump(result, outfile, indent=2, ensure_ascii=False)