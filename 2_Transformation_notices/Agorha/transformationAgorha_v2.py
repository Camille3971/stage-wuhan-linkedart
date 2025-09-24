import os
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
    cases = {"bronze":"https://vocab.getty.edu/aat/300010957","porcelaine":"https://vocab.getty.edu/aat/300010662","jade":"https://vocab.getty.edu/aat/300011119","céramique":"https://vocab.getty.edu/aat/300235507","soie":"https://vocab.getty.edu/aat/300014072","terre":"https://vocab.getty.edu/aat/300020133","céladon":"https://vocab.getty.edu/aat/300015100","noir de carbone":"https://vocab.getty.edu/aat/300013138","ocre":"https://vocab.getty.edu/aat/300013385","hématite":"https://vocab.getty.edu/aat/300011105","carbonate de calcium":"https://vocab.getty.edu/aat/300212174","argile":"https://vocab.getty.edu/aat/300010439","quartz":"https://vocab.getty.edu/aat/300011132","noir d'os":"https://vocab.getty.edu/aat/300013147","argent":"https://vocab.getty.edu/aat/300011029","biscuit":"https://vocab.getty.edu/aat/300242297","bistre":"https://vocab.getty.edu/aat/300013351","pierre":"https://vocab.getty.edu/aat/300011670","or":"https://vocab.getty.edu/aat/300011021","cuivre":"https://vocab.getty.edu/aat/300011020","marbre":"https://vocab.getty.edu/aat/300011443","vermillon":"https://vocab.getty.edu/aat/300013568","bleu de fer":"https://vocab.getty.edu/aat/300013315","sulfate de calcium":"https://vocab.getty.edu/aat/300011099","oxyde de plomb":"https://vocab.getty.edu/aat/300013921","peinture":"https://vocab.getty.edu/aat/300015029","papier":"https://vocab.getty.edu/aat/300014110","carton-pâte":"https://vocab.getty.edu/aat/300014224"}
    label_clean = label.strip().lower()
    for key, uri in cases.items():
        clean_key = key.strip().lower()
        if clean_key in label_clean:
            return uri
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

        

def get_current_location_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"Louvre":"https://vocab.getty.edu/ulan/500125189","Fondation des artistes":"https://www.wikidata.org/wiki/Q3075687","Localisation inconnue":"Localisation inconnue","Bibliothèque municipale (Lyon)":"https://www.wikidata.org/wiki/Q8622","Unknown":"Localisation inconnue","Musée Angladon":"https://vocab.getty.edu/ulan/500265588","BnF":"https://vocab.getty.edu/ulan/500309981","Guimet":"https://vocab.getty.edu/ulan/500275906","Metropolitan Museum of Art":"https://vocab.getty.edu/ulan/500125157","Cernuschi":"https://www.wikidata.org/wiki/Q1667022"})
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

def get_took_place_at_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"chine": "http://vocab.getty.edu/tgn/1000111"})
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

def get_current_owner_uri(label):
    result = get_getty_uri_from_label(label, special_cases={"Louvre":"https://vocab.getty.edu/ulan/500125189", "Bibliothèque nationale de France":"https://vocab.getty.edu/ulan/500309981","Heidelberg":"https://vocab.getty.edu/ulan/500307995","Ministère de la Culture":"https://vocab.getty.edu/ulan/500257707","Asia Art Archive":"https://www.wikidata.org/wiki/Q4806343","Metropolitan Museum of Art":"https://vocab.getty.edu/ulan/500125157","Academia.edu":"https://www.wikidata.org/wiki/Q2777905","Paris Musées":"https://www.wikidata.org/wiki/Q3365279"})
    if result:
        return result
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def conversion_agorha_to_linkedart(data):
    def extract_created_by(data):
        produced = data["crm:P108i_was_produced_by"]
        if produced:
            if not isinstance(produced,list):
                produced = [produced]
            author = produced[0].get("crm:P14_carried_out_by")
            if author:
                author = author.get("rdfs:label")
                if author:
                    return [{
                        "id": get_carried_out_by_uri(author),
                        "_label": author,
                    }]
        return [{
            "id": NOT_SPECIFIED_URI,
            "_label": "Not Specified",
        }]

    def extract_production_place_payload(data):
        productions = data.get("crm:P108i_was_produced_by")

        if not productions:
            return None

        # S’assurer qu’il s’agit d’une liste pour un traitement uniforme
        if not isinstance(productions, list):
            productions = [productions]

        for production in productions:
            place = production.get("crm:P7_took_place_at")
            if place:
                identified_by = place.get("crm:P1_is_identified_by")
                if not isinstance(identified_by, list):
                    identified_by = [identified_by]

                label_container = identified_by[0].get("crm:P87_is_identified_by")
                if isinstance(label_container, dict):
                    label = label_container.get("rdfs:label")
                    if isinstance(label, str):
                        return {
                            "id": get_took_place_at_uri(label),
                            "type": "Place",
                            "_label": label
                        }
        return {
            "id": NOT_SPECIFIED_URI,
            "type": "Place",
            "_label": "Not Specified"
        }

    def extract_identified_by_payload(data):
        identified_by = [
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
                "content": data.get("crm:P102_has_title")["rdfs:label"]["@value"] 
                if not isinstance(data.get('crm:P102_has_title'), list)
                else data.get("crm:P102_has_title")[0]["rdfs:label"]["@value"],
                "language": [
                    {
                        "id": "http://vocab.getty.edu/page/aat/300388306",
                        "type": "Language",
                        "_label": "French",
                        "notation": "fr"
                    }
                ]
            },
        ]

        # Récupérer l’identifiant uniquement s’il est présent
        permanent_location = data.get("crm:P54_has_current_permanent_location")
        if permanent_location:
            if isinstance(permanent_location, list):
                content = data["crm:P54_has_current_permanent_location"][1].get("crm:P87_is_identified_by")
                if content:
                    content = content["rdfs:label"]
                else:
                    content = permanent_location[1]["crm:P3_has_note"]

            elif isinstance(permanent_location["crm:P87_is_identified_by"], list):
                content = permanent_location["crm:P87_is_identified_by"][1]['rdfs:label']
            else:
                content = data["crm:P54_has_current_permanent_location"]["crm:P87_is_identified_by"]["crm:P1_is_identified_by"]["crm:P87_is_identified_by"]["rdfs:label"]
            identified_by.append(
                {
                    "type": "Identifier",
                    "classified_as": [
                        {
                            "id": "http://vocab.getty.edu/aat/300312355",
                            "type": "Type",
                            "_label": "Accession Number"
                        }
                    ],
                    "content": content                
                }
            )
        return identified_by

    def extract_owner(data):
        refered_to_by = data.get("crm:P67i_is_referred_to_by")
        if refered_to_by:
            if not isinstance(refered_to_by,list):
                refered_to_by = [refered_to_by]
            for item in refered_to_by:
                current_owner = item.get("crm:P51_has_former_or_current_owner")
                if current_owner:
                    owner = current_owner["rdfs:label"]
                    return [
                        {
                            "id": get_current_owner_uri(owner),
                            "type": "Group",
                            "_label": owner,
                        }
                    ]
        return [
            {
                "id":NOT_SPECIFIED_URI,
                "type": "Group",
                "_label": "Not Specified",
            }
        ]

    def extract_collection(data):
        if data.get("crm:P24i_changed_ownership_through"):
            ownership_list = data["crm:P24i_changed_ownership_through"]
            if not isinstance(ownership_list,list):
                ownership_list = [ownership_list]

            for owner in ownership_list:
                refers_to = owner.get("crm:P67_refers_to")
                if refers_to:
                    if isinstance(refers_to, list):
                        refers_to = refers_to[0]
                    return [{
                            "id": refers_to["rdfs:label"],
                            "type": "Set",
                            "_label": refers_to["rdfs:label"]
                            }]

        return [{
                "id":NOT_SPECIFIED_URI,
                "type": "Group",
                "_label": "Not Specified"
        }]

    def extract_timespan(data):
        production_data = data.get("crm:P108i_was_produced_by")
        if isinstance(production_data, list):
            production_event = production_data[1]
        else:
            production_event = production_data
        time_span = production_event.get("crm:P4_has_time-span", {}) if production_event else {}

        label = (
            time_span
            .get("crm:P115_finishes", {})
            .get("crm:P78_is_identified_by", {})
            .get("crm:P1_is_identified_by", {})
            .get("rdfs:label", {})
            .get("@value", "Not Specified")
        )

        begin_of_the_begin = time_span.get("crm:P82a_begin_of_the_begin", "Not Specified")
        end_of_the_end = time_span.get("crm:P82b_end_of_the_end", "Not Specified")

        return {
            "type": "TimeSpan",
            "_label": label,
            "begin_of_the_begin": begin_of_the_begin,
            "end_of_the_end": end_of_the_end,
        }

    def extract_materials(data):
        materials = []

        concerned = data.get("crm:P34_concerned")
        if not concerned:
            return materials

        if isinstance(concerned, list):
            concerned = concerned[-1]
        consists_of = concerned.get("crm:P45_consists_of")
        if not consists_of:
            return materials

        identified_by = consists_of.get("crm:P1_is_identified_by")
        if not identified_by:
            return materials

        if isinstance(identified_by, dict):
            identified_by = [identified_by]

        for material in identified_by:
            label_data = material.get("rdfs:label", {})

            if isinstance(label_data, dict):
                label = label_data.get("@value", "")
            else:
                label = ""

            materials.append({
                "id": get_material_uri(label),
                "type": "Material",
                "_label": label
            })

        return materials

    def extract_current_location(data):
        permanent_location = data.get("crm:P54_has_current_permanent_location")
        if permanent_location:
            # Si ce n’est pas une liste, la rendre uniforme
            if not isinstance(permanent_location, list):
                permanent_location = [permanent_location]
            
            id_by = permanent_location[0].get("crm:P87_is_identified_by")
            if not isinstance(id_by, list):
                id_by = [id_by]
            
            value = id_by[0].get("crm:P1_is_identified_by")
            if value:
                value = value["crm:P87_is_identified_by"]["rdfs:label"]
                return [{
                    "id": get_current_location_uri(value),
                    "type": "Place",
                    "_label": value
                }]

        return [{
               "id": "Unknown",
               "type": "Place",
               "_label": "Unknown"
        }]
    
    def extract_dimensions(data):
        dimensions_raw = data.get("crm:P43_has_dimension", [])
        if not isinstance(dimensions_raw, list):
            dimensions_raw = [dimensions_raw]

        dimension_list = []

        label_mapping = {
            0: {"id": "http://vocab.getty.edu/aat/300055644", "_label": "Height"},
            1: {"id": "http://vocab.getty.edu/aat/300055644", "_label": "Length"},
            2: {"id": "http://vocab.getty.edu/aat/300055647", "_label": "Width"},
        }

        for i, dim in enumerate(dimensions_raw):
            value = dim.get("crm:P90_has_value")
            if not value:
                continue

            # Extraire le label de l’unité
            unit_data = dim.get("crm:P91_has_unit")
            unit_label = unit_data["rdfs:label"] if unit_data and "rdfs:label" in unit_data else "centimeters"
            unit_id = "http://vocab.getty.edu/aat/300379098"

            dimension_entry = {
                "type": "Dimension",
                "classified_as": [{
                    "id": label_mapping.get(i, {}).get("id", "http://vocab.getty.edu/aat/300055646"),
                    "type": "Type",
                    "_label": label_mapping.get(i, {}).get("_label", "Dimension")
                }],
                "value": value,
                "unit": {
                    "id": unit_id,
                    "type": "MeasurementUnit",
                    "_label": unit_label
                }
            }

            dimension_list.append(dimension_entry)

        return dimension_list

    # On récupère la première note avec @value
    note_content = None
    for ref in data.get("crm:P67i_is_referred_to_by", []):
        if isinstance(ref, str):
            note_content = ref
            break
        note = ref.get("crm:P3_has_note")
        if isinstance(note, dict) and "@value" in note:
            note_content = note["@value"]
            break

    result = {
        "@context": "https://linked.art/ns/v1/linked-art.json",
        "id": data.get("@id"),
        "type": "HumanMadeObject",
        "_label": data.get("crm:P102_has_title")["rdfs:label"]["@value"] 
        if not isinstance(data.get('crm:P102_has_title'), list)
        else data.get("crm:P102_has_title")[0]["rdfs:label"]["@value"],


        # Informations générales sur l'oeuvre
        # "identified_by" : Titre, numéro d'inventaire et typologie de l'oeuvre
        "identified_by": extract_identified_by_payload(data),

        # "produced_by" : Date, lieu de création et auteur
        "produced_by": [
            {
                "type": "Production",
                "timespan": extract_timespan(data),
                "took_place_at": [
                    extract_production_place_payload(data)
                ],
                "carried_out_by": extract_created_by(data),
            },
        ],

        "member_of": extract_collection(data),

        # Informations physiques sur l'oeuvre
        # "made_of" : Matériaux
        "made_of": extract_materials(data),

        # "dimension" : dimensions longueur, hauteur, largeur
        "dimension": extract_dimensions(data),

        # "referred_to_by" : commentaire
        "referred_to_by": [{
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
            "content": note_content,
        }],

        
        
        # Informations sur l'état juridique de l'oeuvre
        # "current_owner" : propriétaire
        "current_owner": extract_owner(data),

        # "current_location" : Emplacement actuel
        "current_location": extract_current_location(data),

        # "changed_ownership_through" : détenteur précédent, mode d’acquisition et date d’acquisition
        "changed_ownership_through": ([
            {
                "type": data["crm:P24i_changed_ownership_through"][2]["crm:P67_refers_to"]["rdfs:label"],
                "_label": data["crm:P24i_changed_ownership_through"][2]["crm:P67_refers_to"]["rdfs:label"],
            }
        if isinstance(data.get("crm:P24i_changed_ownership_through"), list) and len(data["crm:P24i_changed_ownership_through"]) >= 3 
        and data["crm:P24i_changed_ownership_through"][2].get("crm:P67_refers_to") else {
            "type": "Not Specified",
            "_label": "Not Specified"
        }]) if data.get("crm:P24i_changed_ownership_through") else
        [{
            "type": "Non Existant",
            "_label": "Non Existant"
        }]
    }

    return result


# Lancement de la transformation 
input_dir = "input_agorha"
output_dir = "output_agorha"
os.makedirs(output_dir, exist_ok=True)

# Lecture du dossier source
n = 0
for f in os.listdir(input_dir):
    if f.endswith(".jsonld"):
        with open(os.path.join(input_dir, f), "r", encoding="utf-8") as infile:
            data = json.load(infile)

        # Conversion
        result = conversion_agorha_to_linkedart(data)

        # Ecriture des fichiers Linked Art
        with open(os.path.join(output_dir, f.replace(".jsonld", "_linkedart.jsonld")), "w", encoding="utf-8") as outfile:
            json.dump(result, outfile, indent=2, ensure_ascii=False)