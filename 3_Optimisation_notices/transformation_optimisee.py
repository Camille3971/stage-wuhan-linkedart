import json, os, sys, requests, re, concurrent.futures

from urllib.parse import urlencode
from SPARQLWrapper import SPARQLWrapper, JSON

NOT_SPECIFIED_URI = 'http://example.org/not_specified'
NOT_FOUND_URI = 'http://example.org/not_found'
NOT_EXPOSED_URI = 'http://example.org/not_exposed'

def get_getty_uri_from_label(label, special_cases=None):
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
    # -----
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

def uri_searcher(label, key, museum="louvre"):
    if label == "Not Specified":
        return NOT_SPECIFIED_URI

    if museum == "louvre":
        special_cases_per_key = {
            "took_place_at": {"chine": "http://vocab.getty.edu/tgn/1000111"},
            "member_of":{"Département des Antiquités égyptiennes":"https://www.wikidata.org/wiki/Q3044749","Département des Objets d'art du Moyen Age, de la Renaissance et des temps modernes":"https://www.wikidata.org/wiki/Q3044767","Service de l'Histoire du Louvre":"https://www.wikidata.org/wiki/Q106824040","Département des Arts de l'Islam":"https://www.wikidata.org/wiki/Q3044748","Musée national Eugène-Delacroix":"https://vocab.getty.edu/ulan/500310018","Département des Arts graphiques":"https://www.wikidata.org/wiki/Q3044753"},
            "current_owner": {"etat": "http://vocab.getty.edu/tgn/1000070","Musées Nationaux Récupération":"https://www.wikidata.org/wiki/Q19013512"},
            "current_permanent_custodian":{"louvre": "http://vocab.getty.edu/ulan/500125189","Union centrale des Arts Décoratifs":"https://vocab.getty.edu/ulan/500256748","Delacroix":"https://vocab.getty.edu/ulan/500310018"},
            "current_custodian": {"louvre":"http://vocab.getty.edu/ulan/500125189","Guimet":"https://vocab.getty.edu/ulan/500275906","Versailles":"https://vocab.getty.edu/ulan/500312482","FNAGP":"https://www.wikidata.org/wiki/Q3075687"},
            "current_location": {"non exposé": NOT_EXPOSED_URI,"Denon":"http://vocab.getty.edu/ulan/500125189","Sully":"http://vocab.getty.edu/ulan/500125189","Versailles":"https://vocab.getty.edu/ulan/500312482","Guimet":"https://vocab.getty.edu/ulan/500275906","FNAGP":"https://www.wikidata.org/wiki/Q3075687","Napoléon":"http://vocab.getty.edu/ulan/500125189","Richelieu":"http://vocab.getty.edu/ulan/500125189", "Abu Dhabi":"https://www.wikidata.org/wiki/Q3176133","Strasbourg":"https://www.wikidata.org/wiki/Q630461","Delacroix":"https://vocab.getty.edu/ulan/500310018","petit format":"http://vocab.getty.edu/ulan/500125189","Réserve Edmond de Rothschild":"http://vocab.getty.edu/ulan/500125189","Réserve des autographes":"http://vocab.getty.edu/ulan/500125189","Réserve des petits albums":"http://vocab.getty.edu/ulan/500125189"},
            "made_of": {"textile":"http://vocab.getty.edu/aat/300231566","acier":"http://vocab.getty.edu/aat/300133751","agate":"http://vocab.getty.edu/aat/300011135","bambou":"http://vocab.getty.edu/aat/300011873","bois":"http://vocab.getty.edu/aat/300011915","bronze":"http://vocab.getty.edu/aat/300010957","burgau":"https://vocab.getty.edu/ulan/500296560","coton":"http://vocab.getty.edu/aat/300014067","cristal de roche":"http://vocab.getty.edu/aat/300011152","cuivre":"http://vocab.getty.edu/aat/300011020","faïence":"http://vocab.getty.edu/aat/300265183","ivoire":"http://vocab.getty.edu/aat/300011857","jade":"http://vocab.getty.edu/aat/300011119","jadéite":"http://vocab.getty.edu/aat/300011119","jaspe":"http://vocab.getty.edu/aat/300011151","métal":"http://vocab.getty.edu/aat/300010900","onyx":"http://vocab.getty.edu/aat/300011337","papier":"http://vocab.getty.edu/aat/300014110","pierre":"http://vocab.getty.edu/aat/300011670","porcelaine":"http://vocab.getty.edu/aat/300010662","soie":"http://vocab.getty.edu/aat/300014072","terre cuite":"http://vocab.getty.edu/aat/300020133","verre":"http://vocab.getty.edu/aat/300010799"},
        }

        # Cas Particulier pour Louvre
        if key == "made_of":
            match = re.search(r"Matériau\s*:\s*(.*?)(\r?\n|$)", label)
            if match:
                label = match.group(1)

    elif museum == "paris_musees":
        special_cases_per_key = {
            "took_place_at": {"chine": "http://vocab.getty.edu/tgn/1000111"},
            "current_location": {"Cernuschi":"https://www.wikidata.org/wiki/Q1667022","Petit Palais":"https://vocab.getty.edu/ulan/500310009","Cognacq-Jay":"https://vocab.getty.edu/ulan/500309999","Galliera":"https://www.wikidata.org/wiki/Q1632912","Carnavalet":"https://vocab.getty.edu/ulan/500214785"},
            "member_of":{"Département des Antiquités égyptiennes":"https://www.wikidata.org/wiki/Q3044749","Département des Objets d'art du Moyen Age, de la Renaissance et des temps modernes":"https://www.wikidata.org/wiki/Q3044767","Service de l'Histoire du Louvre":"https://www.wikidata.org/wiki/Q106824040","Département des Arts de l'Islam":"https://www.wikidata.org/wiki/Q3044748","Musée national Eugène-Delacroix":"https://vocab.getty.edu/ulan/500310018","Département des Arts graphiques":"https://www.wikidata.org/wiki/Q3044753"},
            "current_owner": {"etat": "http://vocab.getty.edu/tgn/1000070","Musées Nationaux Récupération":"https://www.wikidata.org/wiki/Q19013512"},
            "current_permanent_custodian":{"louvre": "http://vocab.getty.edu/ulan/500125189","Union centrale des Arts Décoratifs":"https://vocab.getty.edu/ulan/500256748","Delacroix":"https://vocab.getty.edu/ulan/500310018"},
            "current_custodian": {"louvre":"http://vocab.getty.edu/ulan/500125189","Guimet":"https://vocab.getty.edu/ulan/500275906","Versailles":"https://vocab.getty.edu/ulan/500312482","FNAGP":"https://www.wikidata.org/wiki/Q3075687"},
            "made_of": {"bronze":"https://vocab.getty.edu/aat/300010957","céramique":"https://vocab.getty.edu/aat/300235507","porcelaine":"https://vocab.getty.edu/aat/300010662","laque":"https://vocab.getty.edu/aat/300014916","bois":"https://vocab.getty.edu/aat/300011915","jade":"https://vocab.getty.edu/aat/300011119","grès":"https://vocab.getty.edu/aat/300011383","crin":"https://vocab.getty.edu/aat/300011819","soie":"https://vocab.getty.edu/aat/300014072","paillette":"https://vocab.getty.edu/aat/300014655","ecaille":"https://vocab.getty.edu/aat/300425558","métal":"https://vocab.getty.edu/aat/300010900","nacre":"https://vocab.getty.edu/aat/300011835","ivoire":"https://vocab.getty.edu/aat/300011857","argent":"https://vocab.getty.edu/aat/300011029","papier":"https://vocab.getty.edu/aat/300014110","gouache":"https://vocab.getty.edu/aat/300070114","velours":"https://vocab.getty.edu/aat/300014080","feuille d'or":"https://vocab.getty.edu/aat/300264831"},
        }

        # Cas Particulier pour Paris Musées
        if key == "made_of":
            label_clean = label.strip().lower()
            for key, uri in special_cases_per_key.get(key,{}).items():
                clean_key = key.strip().lower()
                if clean_key in label_clean:
                    return uri
            if label:
                return NOT_FOUND_URI
            return NOT_SPECIFIED_URI

    elif museum == "agorha":
        special_cases_per_key = {
            "took_place_at": {"chine": "http://vocab.getty.edu/tgn/1000111"},
            "current_location": {"Louvre":"https://vocab.getty.edu/ulan/500125189","Fondation des artistes":"https://www.wikidata.org/wiki/Q3075687","Localisation inconnue":NOT_EXPOSED_URI,"Bibliothèque municipale (Lyon)":"https://www.wikidata.org/wiki/Q8622","Unknown":NOT_EXPOSED_URI,"Musée Angladon":"https://vocab.getty.edu/ulan/500265588","BnF":"https://vocab.getty.edu/ulan/500309981","Guimet":"https://vocab.getty.edu/ulan/500275906","Metropolitan Museum of Art":"https://vocab.getty.edu/ulan/500125157","Cernuschi":"https://www.wikidata.org/wiki/Q1667022"},
            "current_owner": {"Louvre":"https://vocab.getty.edu/ulan/500125189", "Bibliothèque nationale de France":"https://vocab.getty.edu/ulan/500309981","Heidelberg":"https://vocab.getty.edu/ulan/500307995","Ministère de la Culture":"https://vocab.getty.edu/ulan/500257707","Asia Art Archive":"https://www.wikidata.org/wiki/Q4806343","Metropolitan Museum of Art":"https://vocab.getty.edu/ulan/500125157","Academia.edu":"https://www.wikidata.org/wiki/Q2777905","Paris Musées":"https://www.wikidata.org/wiki/Q3365279"},
            "member_of":{"Département des Antiquités égyptiennes":"https://www.wikidata.org/wiki/Q3044749","Département des Objets d'art du Moyen Age, de la Renaissance et des temps modernes":"https://www.wikidata.org/wiki/Q3044767","Service de l'Histoire du Louvre":"https://www.wikidata.org/wiki/Q106824040","Département des Arts de l'Islam":"https://www.wikidata.org/wiki/Q3044748","Musée national Eugène-Delacroix":"https://vocab.getty.edu/ulan/500310018","Département des Arts graphiques":"https://www.wikidata.org/wiki/Q3044753"},
            "current_permanent_custodian":{"louvre": "http://vocab.getty.edu/ulan/500125189","Union centrale des Arts Décoratifs":"https://vocab.getty.edu/ulan/500256748","Delacroix":"https://vocab.getty.edu/ulan/500310018"},
            "current_custodian": {"louvre":"http://vocab.getty.edu/ulan/500125189","Guimet":"https://vocab.getty.edu/ulan/500275906","Versailles":"https://vocab.getty.edu/ulan/500312482","FNAGP":"https://www.wikidata.org/wiki/Q3075687"},
            "made_of": {"bronze":"https://vocab.getty.edu/aat/300010957","porcelaine":"https://vocab.getty.edu/aat/300010662","jade":"https://vocab.getty.edu/aat/300011119","céramique":"https://vocab.getty.edu/aat/300235507","soie":"https://vocab.getty.edu/aat/300014072","terre":"https://vocab.getty.edu/aat/300020133","céladon":"https://vocab.getty.edu/aat/300015100","noir de carbone":"https://vocab.getty.edu/aat/300013138","ocre":"https://vocab.getty.edu/aat/300013385","hématite":"https://vocab.getty.edu/aat/300011105","carbonate de calcium":"https://vocab.getty.edu/aat/300212174","argile":"https://vocab.getty.edu/aat/300010439","quartz":"https://vocab.getty.edu/aat/300011132","noir d'os":"https://vocab.getty.edu/aat/300013147","argent":"https://vocab.getty.edu/aat/300011029","biscuit":"https://vocab.getty.edu/aat/300242297","bistre":"https://vocab.getty.edu/aat/300013351","pierre":"https://vocab.getty.edu/aat/300011670","or":"https://vocab.getty.edu/aat/300011021","cuivre":"https://vocab.getty.edu/aat/300011020","marbre":"https://vocab.getty.edu/aat/300011443","vermillon":"https://vocab.getty.edu/aat/300013568","bleu de fer":"https://vocab.getty.edu/aat/300013315","sulfate de calcium":"https://vocab.getty.edu/aat/300011099","oxyde de plomb":"https://vocab.getty.edu/aat/300013921","peinture":"https://vocab.getty.edu/aat/300015029","papier":"https://vocab.getty.edu/aat/300014110","carton-pâte":"https://vocab.getty.edu/aat/300014224"},
        }

        # Cas Particulier pour Agorha
        if key == "made_of":
            label_clean = label.strip().lower()
            for key, uri in special_cases_per_key.get(key,{}).items():
                clean_key = key.strip().lower()
                if clean_key in label_clean:
                    return uri
            if label:
                return NOT_FOUND_URI
            return NOT_SPECIFIED_URI

    special_cases = special_cases_per_key.get(key, {})
    result = get_getty_uri_from_label(label, special_cases=special_cases)
    if result:
        return result
    
    if label:
        return NOT_FOUND_URI
    return NOT_SPECIFIED_URI

def create_intermediate_representation_agorha(data):
    def get_inventory_number(data):
        permanent_location = data.get("crm:P54_has_current_permanent_location")
        if permanent_location:
            # IVoir si c'est une liste
            if isinstance(permanent_location, list):
                content = data["crm:P54_has_current_permanent_location"][1].get("crm:P87_is_identified_by")
                if content:
                    content = content["rdfs:label"]
                else:
                    content = permanent_location[1]["crm:P3_has_note"]
            # Pas de liste externe mais une liste interne
            elif isinstance(permanent_location["crm:P87_is_identified_by"], list):
                content = permanent_location["crm:P87_is_identified_by"][1]['rdfs:label']
            else:
                content = data["crm:P54_has_current_permanent_location"]["crm:P87_is_identified_by"]["crm:P1_is_identified_by"]["crm:P87_is_identified_by"]["rdfs:label"]
            return content
        return "Not Specified"
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
            "creation_date": label,
            "beginning": begin_of_the_begin,
            "end": end_of_the_end,
        }

    def extract_place_of_creation(data):
        productions = data.get("crm:P108i_was_produced_by")

        if not productions:
            return None

        # S’assurer que c’est une liste pour un traitement uniforme
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
                        return label
        return "Not Specified"

    def extract_creator(data):
        produced = data["crm:P108i_was_produced_by"]
        if produced:
            if not isinstance(produced,list):
                produced = [produced]
            author = produced[0].get("crm:P14_carried_out_by")
            if author:
                author = author.get("rdfs:label")
                if author:
                    return author
        return "Not Specified"

    def extract_dimensions(data):
        dimensions_raw = data.get("crm:P43_has_dimension", [])
        if not isinstance(dimensions_raw, list):
            dimensions_raw = [dimensions_raw]

        dimension_list = []

        for i, dim in enumerate(dimensions_raw):
            value = dim.get("crm:P90_has_value")
            if not value:
                continue

            unit_data = dim.get("crm:P91_has_unit")
            unit_label = unit_data["rdfs:label"] if unit_data and "rdfs:label" in unit_data else "centimeters"

            dimension_entry = {
                "value": value,
                "unit": unit_label
            }

            dimension_list.append(dimension_entry)

        return dimension_list

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

            materials.append(label)

        return materials

    def extract_owner(data):
        refered_to_by = data.get("crm:P67i_is_referred_to_by")
        if refered_to_by:
            if not isinstance(refered_to_by,list):
                refered_to_by = [refered_to_by]
            for item in refered_to_by:
                current_owner = item.get("crm:P51_has_former_or_current_owner")
                if current_owner:
                    owner = current_owner["rdfs:label"]
                    return owner
                    
        return "Not Specified"

    def extract_object_description(data):
        for ref in data.get("crm:P67i_is_referred_to_by", []):
            if isinstance(ref, str):
                return ref
            note = ref.get("crm:P3_has_note")
            if isinstance(note, dict) and "@value" in note:
                return note["@value"]

    def extract_collection(data):
        if data.get("crm:P24i_changed_ownership_through"):
            ownership_list = data["crm:P24i_changed_ownership_through"]

            # Transformer en liste si besoin
            if not isinstance(ownership_list,list):
                ownership_list = [ownership_list]

            for owner in ownership_list:
                refers_to = owner.get("crm:P67_refers_to")
                if refers_to:
                    if isinstance(refers_to, list):
                        refers_to = refers_to[0]
                    return refers_to["rdfs:label"]

        return "Not Specified"

    def extract_current_location(data):
        permanent_location = data.get("crm:P54_has_current_permanent_location")
        if permanent_location:
            # Transformer en liste si besoin
            if not isinstance(permanent_location, list):
                permanent_location = [permanent_location]
            
            # Transformer en liste si besoin
            id_by = permanent_location[0].get("crm:P87_is_identified_by")
            if not isinstance(id_by, list):
                id_by = [id_by]
            
            value = id_by[0].get("crm:P1_is_identified_by")
            if value:
                value = value["crm:P87_is_identified_by"]["rdfs:label"]
                return value

        return "Not Specified"

    def extract_mode_of_transfer(data):
        changed_ownership = data.get("crm:P24i_changed_ownership_through")
        if changed_ownership:
            if isinstance(changed_ownership, list) and len(changed_ownership) >= 3 and changed_ownership[2].get("crm:P67_refers_to"):
                return data["crm:P24i_changed_ownership_through"][2]["crm:P67_refers_to"]["rdfs:label"]

        return "Not Specified"


    dimension_list = extract_dimensions(data)

    height = dimension_list[0]['value'] if len(dimension_list) > 0 else "Not Specified"
    lenght = dimension_list[1]['value'] if len(dimension_list) > 1 else "Not Specified"
    width = dimension_list[2]['value'] if len(dimension_list) > 2 else "Not Specified"

    height_unit = dimension_list[0]['unit'] if len(dimension_list) > 0 else "Not Specified"
    lenght_unit = dimension_list[1]['unit'] if len(dimension_list) > 1 else "Not Specified"
    width_unit = dimension_list[2]['unit'] if len(dimension_list) > 2 else "Not Specified"

    struct = {
        "data_source": "agorha",
        "id": data['@id'],
        "title": data.get("crm:P102_has_title")["rdfs:label"]["@value"] 
        if not isinstance(data.get('crm:P102_has_title'), list)
        else data.get("crm:P102_has_title")[0]["rdfs:label"]["@value"],
        "inventory_number": get_inventory_number(data),
        "timespan": extract_timespan(data),
        "place_of_creation": extract_place_of_creation(data),
        "creator": extract_creator(data),
        "collection": extract_collection(data),
        "width":width,
        "height":height,
        "length":lenght,
        "width_unit":width_unit,
        "height_unit":height_unit,
        "length_unit": lenght_unit,
        "materials": extract_materials(data),
        "object_description": extract_object_description(data),
        "owner": extract_owner(data),
        "current_permanent_custodian": "Not Specified",
        "current_custodian": "Not Specified",
        "current_location": extract_current_location(data),
        "changed_ownership_through": {
            "mode_of_transfer": extract_mode_of_transfer(data),
            "timespan_beginning": "xxxx",
            "timespan_end": "xxxx",
            "previous_owner":"Not Specified"
        } if data.get('crm:P24i_changed_ownership_through') else None,
        "exhibition": "Not Specified",
    }

    return struct

def create_intermediate_representation_paris_musees(data):
    # Default Case
    materials_list = ["Not Specified"]
    if data.get("queryFieldMateriauxTechnique"):
        materials_list = data.get("queryFieldMateriauxTechnique", {}).get("entities", [])
        materials_list = filter(lambda e: e.get('entityLabel'), materials_list)
        materials_list = map(lambda e: e.get('entityLabel'), materials_list)

    struct = {
        "data_source": "paris_musees",
        "id": data["absolutePath"],
        "title": data["title"],
        "inventory_number": data.get("fieldOeuvreNumInventaire") if data.get("fieldOeuvreNumInventaire") else None,
        "timespan": {
            "creation_date": data.get("fieldOeuvreSiecle", {}).get("entity", {}).get("entityLabel") if isinstance(data.get("fieldOeuvreSiecle"), dict) else None,
            "beginning": str(data.get("fieldDateProduction", {}).get("startYear")) if isinstance(data.get("fieldDateProduction"), dict) else None,
            "end": str(data.get("fieldDateProduction", {}).get("endYear")) if isinstance(data.get("fieldDateProduction"), dict) else None
        },
        "place_of_creation": "Chine",
        "creator": data.get("fieldAuteurAuteur")["entity"]["entityLabel"] if data.get("fieldAuteurAuteur") and len( data["fieldAuteurAuteur"]) > 0 else "Not Specified",
        "collection": "Not Specified",
        "width":data.get("fieldOeuvreDimensions")[1]["entity"]["fieldDimensionValeur"]  if data.get("fieldOeuvreDimensions") and len( data["fieldOeuvreDimensions"]) > 1 else None,
        "height":data.get("fieldOeuvreDimensions")[0]["entity"]["fieldDimensionValeur"] if data.get("fieldOeuvreDimensions") and len( data["fieldOeuvreDimensions"]) > 0 else None,
        "length":data.get("fieldOeuvreDimensions")[2]["entity"]["fieldDimensionValeur"] if data.get("fieldOeuvreDimensions") and len( data["fieldOeuvreDimensions"]) > 2 else None,
        "width_unit":"centimeters",
        "height_unit":"centimeters",
        "length_unit": "centimeters",
        "materials": materials_list,
        "object_description": data.get("fieldOeuvreDescriptionIcono")["value"] if data.get("fieldOeuvreDescriptionIcono") else None,
        "owner": "Not Specified",
        "current_permanent_custodian": "Not Specified",
        "current_custodian": "Not Specified",
        "current_location": data.get("queryFieldMusee")["entities"][0]["entityLabel"],
        "changed_ownership_through": {
            "mode_of_transfer": data.get("queryFieldModaliteAcquisition", {}).get("entities", [{}])[0].get("entityLabel", "Not Specified"),
            "timespan_beginning": "xxxx",
            "timespan_end": "xxxx",
            "previous_owner": data.get("queryFieldDonateurs", {}).get("entities", [{}])[0].get("entityLabel", "Not Specified"),
        } if data.get('queryFieldDonateurs') else None,
        "exhibition": "Not Specified",
    }

    return struct

def create_intermediate_representation_louvre(data):
    struct = {
        "data_source": "louvre",
        "id": data["url"],
        "title": data["title"],
        "inventory_number": data.get("objectNumber")[0]["value"] if data.get("objectNumber") else None,
        "timespan": {
            "creation_date": data.get("dateCreated")[0]["text"] if data.get("dateCreated") else None,
            "beginning": str(data.get("dateCreated")[0]["startYear"]) if data.get( "dateCreated") else None,
            "end": str(data.get("dateCreated")[0]["endYear"]) if data.get("dateCreated") else None,
        },
        "place_of_creation": data['placeOfCreation'],
        "creator": data.get("creator")[0]["label"] if data.get("creator") and len( data["creator"]) > 0 else "Not Specified",
        "collection": data['collection'],
        "width":data.get("dimension")[0]["displayDimension"] if data.get("dimension") and len( data["dimension"]) > 0 else None,
        "height":data.get("dimension")[1]["displayDimension"] if data.get("dimension") and len( data["dimension"]) > 1 else None,
        "length":data.get("dimension")[2]["displayDimension"] if data.get("dimension") and len( data["dimension"]) > 2 else None,
        "width_unit":"centimeters",
        "height_unit":"centimeters",
        "length_unit": "centimeters",
        "materials": [
            data['materialsAndTechniques']
        ],
        'object_description': data['description'],
        "owner": data['ownedBy'],
        "current_permanent_custodian": data['heldBy'],
        "current_custodian": data['longTermLoanTo'],
        "current_location": data['currentLocation'],
        "changed_ownership_through": {
            "mode_of_transfer": data.get("acquisitionDetails")[0]['mode'] if data.get("acquisitionDetails") else "Not Specified",
            "timespan_beginning": str(data.get("acquisitionDetails")[0]["dates"][0]["startYear"]) if data.get( "acquisitionDetails") and (len(data.get("acquisitionDetails")[0]["dates"]) != 0) else "xxxx",
            "timespan_end": str(data.get("acquisitionDetails")[0]["dates"][0]["endYear"]) if data.get( "acquisitionDetails") and (len(data.get("acquisitionDetails")[0]["dates"]) != 0) else "xxxx",
            "previous_owner": data["previousOwner"][0]["value"] if data.get("previousOwner") and len( data["previousOwner"]) > 0 else "Not Specified",
        } if len(data['acquisitionDetails']) != 0 else None,
        "exhibition": data.get("exhibition")[0]["value"] if data.get("exhibition") and len(data["exhibition"]) > 0 else None,
    }

    return struct

def intermediate_represantation_to_linkedart(intermediate):
    result = {
        "@context": "https://linked.art/ns/v1/linked-art.json",
        "id": intermediate['id'],
        "type": "HumanMadeObject",
        "_label": intermediate['title'],
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
                "content": intermediate['title'],
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
                "content": intermediate['inventory_number']
            }],
        # "produced_by" : Date, lieu de création et auteur
        "produced_by": [
            {
                "type": "Production",
                "timespan": {
                    "type": "TimeSpan",
                    "_label": intermediate['timespan']['creation_date'],
                    "begin_of_the_begin": intermediate['timespan']['beginning'],
                    "end_of_the_end": intermediate['timespan']['end'],
                },
                "took_place_at": [
                    {
                        "id": "https://vocab.getty.edu/tgn/1000111",
                        "type": "Place",
                        "_label": intermediate['place_of_creation']
                    }
                ],
                "carried_out_by": [
                    {
                        "id": uri_searcher(intermediate['creator'], "carried_out_by", intermediate['data_source']),
                        "_label": intermediate['creator'],
                    }
                ]
            }
        ],
        # "member_of": collection et exposition
        "member_of": [
            {
                "id": uri_searcher(intermediate['collection'], "member_of", intermediate['data_source']),
                "type": "Set",
                "_label": intermediate['collection'],
            },
        ],
        # "made_of" : Matériaux
        "made_of": [
            {
                "id": uri_searcher(material, "made_of", intermediate['data_source']),
                "type": "Material",
                "_label": material
            } for material in intermediate['materials']
        ],
        # "dimension" : dimensions longueur, hauteur, largeur
        "dimension": [
            {
                "type": "Dimension",
                "classified_as": [{"id": "http://vocab.getty.edu/aat/300055647", "type": "Type", "_label": "Width"}],
                "value": intermediate['width'],
                "unit": {"id": uri_searcher(intermediate['width_unit'], "unit", intermediate['data_source']), "type": "MeasurementUnit",
                         "_label": intermediate['width_unit']}
            },
            {
                "type": "Dimension",
                "classified_as": [{"id": "http://vocab.getty.edu/aat/300055644", "type": "Type", "_label": "Height"}],
                "value": intermediate['height'],
                "unit": {"id": uri_searcher(intermediate['height_unit'], "unit", intermediate['data_source']), "type": "MeasurementUnit",
                         "_label": intermediate['height_unit']}
            },
            {
                "type": "Dimension",
                "classified_as": [{"id": "http://vocab.getty.edu/aat/300055644", "type": "Type", "_label": "Length"}],
                "value": intermediate['length'],
                "unit": {"id": uri_searcher(intermediate['length_unit'], "unit", intermediate['data_source']), "type": "MeasurementUnit",
                         "_label": intermediate['length_unit']}
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
                "content": intermediate['object_description']
            }
        ],
        # "current_owner" : propriétaire
        "current_owner": [
            {
                "id": uri_searcher(intermediate['owner'], "current_owner", intermediate['data_source']),
                "type": "Group",
                "_label": intermediate['owner']
            }
        ],
        # "current_permanent_custodian": affectataire
        "current_permanent_custodian": {
            "id": uri_searcher(intermediate["current_permanent_custodian"], "current_permanent_custodian", intermediate['data_source']),
            "type": "Group",
            "_label": intermediate["current_permanent_custodian"],
        },

        # "current_custodian" : dépositaire 
        "current_custodian": [
            {
                "id": uri_searcher(intermediate["current_custodian"], "current_custodian", intermediate['data_source']),
                "type": "Group",
                "_label": intermediate["current_custodian"],
            }
        ],

        # "current_location" : Emplacement actuel
        "current_location": [
            {
                "id": uri_searcher(intermediate['current_location'], "current_location", intermediate['data_source']),
                "type": "Place",
                "_label": intermediate['current_location'],
            }
        ],
    }

    # CAS PARTICULIERS
    # Traitement pour le Louvre
    #-------------------------------------------
    if intermediate['changed_ownership_through']:
        result['changed_ownership_through'] = [
                {
                    "type": "Acquisiton",
                    "_label": intermediate['changed_ownership_through']['mode_of_transfer'],
                    "timespan": {
                        "type": "TimeSpan",
                        "begin_of_the_begin": intermediate['changed_ownership_through']['timespan_beginning'],
                        "end_of_the_end": intermediate['changed_ownership_through']['timespan_end'],
                    },
                    "transferred_title_from": [
                        {
                            "id": uri_searcher(intermediate['changed_ownership_through']['previous_owner'], "transferred_title_from", intermediate['data_source']),
                            "_label": intermediate['changed_ownership_through']['previous_owner']
                        }
                    ]
                }
        ]
    
    if intermediate['exhibition']:
        result['member_of'].append({
                "id": uri_searcher(intermediate['exhibition'], "exhibition", intermediate['data_source']),
                "type": "Set",
                "_label": intermediate['exhibition']
        })

    #-------------------------------------------

    return result

# Pipeline
def process_directory(input_dir, normalizer, prefix):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    for f in os.listdir(input_dir):
        # Obtenir chaque fichier JSON
        if f.endswith(".json") or f.endswith(".jsonld"):
            if f.endswith(".json"):
                extension = ".json"
            if f.endswith(".jsonld"):
                extension = ".jsonld"

            with open(os.path.join(input_dir, f), "r", encoding="utf-8") as infile:
                data = json.load(infile)

            # Normaliser
            intermediate = normalizer(data)

            # Transformer en Linkedart
            result = intermediate_represantation_to_linkedart(intermediate)

            # Sauvgarder l'output
            out_path = os.path.join(output_dir, f.replace(extension, f"_{prefix}_linkedart.jsonld"))
            with open(out_path, "w", encoding="utf-8") as outfile:
                json.dump(result, outfile, indent=2, ensure_ascii=False)

# --- Version Mulithreading

def process_file_mulithread(f, input_dir, normalizer, prefix, output_dir):
    if f.endswith(".json"):
        extension = ".json"
    elif f.endswith(".jsonld"):
        extension = ".jsonld"
    else:
        return

    try:
        with open(os.path.join(input_dir, f), "r", encoding="utf-8") as infile:
            data = json.load(infile)

        # Normaliser l'input
        intermediate = normalizer(data)

        # Transformer en Linkedart
        result = intermediate_represantation_to_linkedart(intermediate)

        # Sauvgarder l'output
        out_path = os.path.join(output_dir, f.replace(extension, f"_{prefix}_linkedart.jsonld"))
        with open(out_path, "w", encoding="utf-8") as outfile:
            json.dump(result, outfile, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error processing {f}: {e}")

def process_directory_mulithread(input_dir, normalizer, prefix, num_threads=8):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(input_dir) if f.endswith((".json", ".jsonld"))]

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(process_file_mulithread, f, input_dir, normalizer, prefix, output_dir)
            for f in files
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()

# --- Init pour chaque dataset ---
if __name__ == "__main__":
    process_directory_mulithread("input_agorha", create_intermediate_representation_agorha, "agorha")
    process_directory_mulithread("input_louvre", create_intermediate_representation_louvre, "louvre")
    process_directory_mulithread("input_parismusees", create_intermediate_representation_paris_musees, "paris_musees")