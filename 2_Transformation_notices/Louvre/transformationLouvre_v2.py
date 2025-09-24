import os
import re
import json
import requests
import sys

from urllib.parse import urlencode
from SPARQLWrapper import SPARQLWrapper, JSON

NOT_SPECIFIED_URI = 'http://example.org/not_specified'
NOT_FOUND_URI = 'http://example.org/not_found'
NOT_EXPOSED_URI = 'http://example.org/not_exposed'

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
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
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


def get_took_place_at_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"chine": "http://vocab.getty.edu/tgn/1000111"})
    if result:
        return result
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def get_member_of_collection_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"Département des Antiquités égyptiennes":"https://www.wikidata.org/wiki/Q3044749","Département des Objets d'art du Moyen Age, de la Renaissance et des temps modernes":"https://www.wikidata.org/wiki/Q3044767","Service de l'Histoire du Louvre":"https://www.wikidata.org/wiki/Q106824040","Département des Arts de l'Islam":"https://www.wikidata.org/wiki/Q3044748","Musée national Eugène-Delacroix":"https://vocab.getty.edu/ulan/500310018","Département des Arts graphiques":"https://www.wikidata.org/wiki/Q3044753"})
    if result:
        return result
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def get_current_owner_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"etat": "http://vocab.getty.edu/tgn/1000070","Musées Nationaux Récupération":"https://www.wikidata.org/wiki/Q19013512"})
    if result:
        return result
    
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI


def get_current_permanent_custodian_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"louvre": "http://vocab.getty.edu/ulan/500125189","Union centrale des Arts Décoratifs":"https://vocab.getty.edu/ulan/500256748","Delacroix":"https://vocab.getty.edu/ulan/500310018"})
    if result:
        return result
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def get_current_custodian_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"louvre":"http://vocab.getty.edu/ulan/500125189","Guimet":"https://vocab.getty.edu/ulan/500275906","Versailles":"https://vocab.getty.edu/ulan/500312482","FNAGP":"https://www.wikidata.org/wiki/Q3075687"})
    if result:
        return result
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def get_current_location_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"non exposé": NOT_EXPOSED_URI,"Denon":"http://vocab.getty.edu/ulan/500125189","Sully":"http://vocab.getty.edu/ulan/500125189","Versailles":"https://vocab.getty.edu/ulan/500312482","Guimet":"https://vocab.getty.edu/ulan/500275906","FNAGP":"https://www.wikidata.org/wiki/Q3075687","Napoléon":"http://vocab.getty.edu/ulan/500125189","Richelieu":"http://vocab.getty.edu/ulan/500125189", "Abu Dhabi":"https://www.wikidata.org/wiki/Q3176133","Strasbourg":"https://www.wikidata.org/wiki/Q630461","Delacroix":"https://vocab.getty.edu/ulan/500310018","petit format":"http://vocab.getty.edu/ulan/500125189","Réserve Edmond de Rothschild":"http://vocab.getty.edu/ulan/500125189","Réserve des autographes":"http://vocab.getty.edu/ulan/500125189","Réserve des petits albums":"http://vocab.getty.edu/ulan/500125189"})
    if result:
        return result
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def get_made_of_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"textile":"http://vocab.getty.edu/aat/300231566","acier":"http://vocab.getty.edu/aat/300133751","agate":"http://vocab.getty.edu/aat/300011135","bambou":"http://vocab.getty.edu/aat/300011873","bois":"http://vocab.getty.edu/aat/300011915","bronze":"http://vocab.getty.edu/aat/300010957","burgau":"https://vocab.getty.edu/ulan/500296560","coton":"http://vocab.getty.edu/aat/300014067","cristal de roche":"http://vocab.getty.edu/aat/300011152","cuivre":"http://vocab.getty.edu/aat/300011020","faïence":"http://vocab.getty.edu/aat/300265183","ivoire":"http://vocab.getty.edu/aat/300011857","jade":"http://vocab.getty.edu/aat/300011119","jadéite":"http://vocab.getty.edu/aat/300011119","jaspe":"http://vocab.getty.edu/aat/300011151","métal":"http://vocab.getty.edu/aat/300010900","onyx":"http://vocab.getty.edu/aat/300011337","papier":"http://vocab.getty.edu/aat/300014110","pierre":"http://vocab.getty.edu/aat/300011670","porcelaine":"http://vocab.getty.edu/aat/300010662","soie":"http://vocab.getty.edu/aat/300014072","terre cuite":"http://vocab.getty.edu/aat/300020133","verre":"http://vocab.getty.edu/aat/300010799"
})
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
    return NOT_SPECIFIED_URI

def extract_main_material(label):
    match = re.search(r"Matériau\s*:\s*(.*?)(\r?\n|$)", label)
    if match:
        return match.group(1)
    return label


def conversion_louvre_to_linkedart(data):
    result = {
        "@context": "https://linked.art/ns/v1/linked-art.json",
        "id": data.get("url"),
        "type": "HumanMadeObject",
        "_label": data.get("title"),

        # Informations générales sur l'oeuvre
        # "identified_by" : Titre, numéro d'inventaire et typologie de l'oeuvre
        "identified_by": [
            {
                "type": "Name",
                "classified_as": [
                    {
                        "id": "http://vocab.getty.edu/aat/300133025",
                        "type": "Type",
                        "_label": "Artwork"
                    },
                    {
                        "id": "http://vocab.getty.edu/aat/300404670",
                        "type": "Type",
                        "_label": "Primary Name"
                    }
                ],
                "content": data.get("title"),
                "language": [
                    {
                        "id": "http://vocab.getty.edu/page/aat/300388306",
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
                        "id": "http://vocab.getty.edu/aat/300312355",
                        "type": "Type",
                        "_label": "Accession Number"
                    }
                ],
                "content": data.get("objectNumber")[0]["value"] if data.get("objectNumber") else None
            }
        ],

        # "produced_by" : Date, lieu de création et auteur
        "produced_by": [
            {
                "type": "Production",
                "timespan": {
                    "type": "TimeSpan",
                    "_label": data.get("dateCreated")[0]["text"] if data.get("dateCreated") else None,
                    "begin_of_the_begin": str(data.get("dateCreated")[0]["startYear"]) if data.get(
                        "dateCreated") else None,
                    "end_of_the_end": str(data.get("dateCreated")[0]["endYear"]) if data.get("dateCreated") else None
                },
                "took_place_at": [
                    {
                        "id": "https://vocab.getty.edu/tgn/1000111",
                        "type": "Place",
                        "_label": data.get("placeOfCreation")
                    }
                ],
                "carried_out_by": [
                    {
                        "id": get_carried_out_by_uri(data.get("creator")[0]["label"] if data.get("creator") and len(
                            data["creator"]) > 0 else NOT_SPECIFIED_URI),
                        "_label": data.get("creator")[0]["label"] if data.get("creator") and len(
                            data["creator"]) > 0 else "Not Specified"
                    }
                ] if data.get("creator") else []
            }
        ],

        # "member_of": collection et exposition
        "member_of": [
            {
                "id": get_member_of_collection_uri(data.get("collection")),
                "type": "Set",
                "_label": data.get("collection")
            },
        ],

        # Informations physiques sur l'oeuvre
        # "made_of" : Matériaux
        "made_of": [
            {
                "id": extract_main_material(data.get("materialsAndTechniques")),
                "type": "Material",
                "_label": data.get("materialsAndTechniques")
            }
        ],

        # "dimension" : dimensions longueur, hauteur, largeur
        "dimension": [
            {
                "type": "Dimension",
                "classified_as": [{"id": "http://vocab.getty.edu/aat/300055647", "type": "Type", "_label": "Width"}],
                "value": data.get("dimension")[0]["displayDimension"] if data.get("dimension") and len(
                    data["dimension"]) > 0 else None,
                "unit": {"id": "http://vocab.getty.edu/aat/300379098", "type": "MeasurementUnit",
                         "_label": "centimeters"}
            },
            {
                "type": "Dimension",
                "classified_as": [{"id": "http://vocab.getty.edu/aat/300055644", "type": "Type", "_label": "Height"}],
                "value": data.get("dimension")[1]["displayDimension"] if data.get("dimension") and len(
                    data["dimension"]) > 1 else None,
                "unit": {"id": "http://vocab.getty.edu/aat/300379098", "type": "MeasurementUnit",
                         "_label": "centimeters"}
            },
            {
                "type": "Dimension",
                "classified_as": [{"id": "http://vocab.getty.edu/aat/300055644", "type": "Type", "_label": "Length"}],
                "value": data.get("dimension")[2]["displayDimension"] if data.get("dimension") and len(
                    data["dimension"]) > 2 else None,
                "unit": {"id": "http://vocab.getty.edu/aat/300379098", "type": "MeasurementUnit",
                         "_label": "centimeters"}
            }
        ],

        # "referred_to_by" : commentaire
        "referred_to_by": [
            {
                "type": "LinguisticObject",
                "classified_as": [
                    {
                        "id": "http://vocab.getty.edu/aat/300435416",
                        "type": "Type",
                        "_label": "Description",
                        "classified_as": [
                            {
                                "id": "http://vocab.getty.edu/aat/300418049",
                                "type": "Type",
                                "_label": "Brief Text"
                            }
                        ]
                    }
                ],
                "content": data.get("description")
            }
        ],

        # Informations sur l'état juridique de l'oeuvre
        # "current_owner" : propriétaire

        "current_owner": [
            {
                "id": get_current_owner_uri(data.get("ownedBy")),
                "type": "Group",
                "_label": data.get("ownedBy")
            }
        ],

        # "current_permanent_custodian": affectataire
        "current_permanent_custodian": {
            "id": get_current_permanent_custodian_uri(data.get("heldBy")),
            "type": "Group",
            "_label": data.get("heldBy")
        },

        # "current_custodian" : dépositaire 
        "current_custodian": [
            {
                "id": get_current_custodian_uri(data.get("longTermLoanTo")),
                "type": "Group",
                "_label": data.get("longTermLoanTo")
            }
        ],

        # "current_location" : Emplacement actuel
        "current_location": [
            {
                "id": get_current_location_uri(data.get("currentLocation")),
                "type": "Place",
                "_label": data.get("currentLocation")
            }
        ],
    }

    # post-processing
    member_of_payload = {
                "id": data.get("exhibition")[0]["value"],
                "type": "Set",
                "_label": data.get("exhibition")[0]["value"],
    } if data.get("exhibition") and len(data["exhibition"]) > 0 else None

    changed_ownership_through = [
            {
                "type": "Acquisiton",
                "_label": data.get("acquisitionDetails")[0]['mode'] if data.get("acquisitionDetails") else "No Ownership Transfer",
                "timespan": {
                    "type": "TimeSpan",
                    "begin_of_the_begin": str(data.get("acquisitionDetails")[0]["dates"][0]["startYear"]) if data.get(
                        "acquisitionDetails") and (len(data.get("acquisitionDetails")[0]["dates"]) != 0) else "xxxx",
                    "end_of_the_end": str(data.get("acquisitionDetails")[0]["dates"][0]["endYear"]) if data.get(
                        "acquisitionDetails") and (len(data.get("acquisitionDetails")[0]["dates"]) != 0) else "xxxx"
                },
                "transferred_title_from": [
                    {
                        "id": get_donateur_uri(data["previousOwner"][0]["value"]) if data.get("previousOwner") and len(
                            data["previousOwner"]) > 0 else NOT_SPECIFIED_URI,
                        "_label": data["previousOwner"][0]["value"] if data.get("previousOwner") and len(
                            data["previousOwner"]) > 0 else "Not Specified"
                    }
                ]
            }
    ]
    
    if len(data.get("acquisitionDetails")) != 0:
        result['changed_ownership_through'] = changed_ownership_through

    if member_of_payload:
        result['member_of'].append(member_of_payload)

    return result


# Lancement de la transformation 
input_dir = "input_louvre"
output_dir = "output_louvre"
os.makedirs(output_dir, exist_ok=True)

# Lecture du dossier source
for f in os.listdir(input_dir):
    if f.endswith(".json"):
        with open(os.path.join(input_dir, f), "r", encoding="utf-8") as infile:
            data = json.load(infile)

        # Conversion
        result = conversion_louvre_to_linkedart(data)

        # Ecriture des fichiers Linked Art
        with open(os.path.join(output_dir, f.replace(".json", "_linkedart.jsonld")), "w", encoding="utf-8") as outfile:
            json.dump(result, outfile, indent=2, ensure_ascii=False)