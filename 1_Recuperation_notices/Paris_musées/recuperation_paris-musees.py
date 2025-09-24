import csv, os, requests
import json
def get_parismusees_json_files():
    def save_entities_to_files(api_response, output_dir="input_paris_musees"):
        # Navigate to entities list
        entities = api_response.get("data", {}).get("nodeQuery", {}).get("entities", [])
        
        # Create folder if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        for entity in entities:
            if entity is None:
                continue
            uuid = entity.get("entityUuid")
            if not uuid:
                continue
            file_path = os.path.join(output_dir, f"{uuid}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(entity, f, ensure_ascii=False, indent=2)
            print(f"Saved: {file_path}")

    def call_parismusees_api(auth_token: str, graphql_query: str):
        """
        Call the Paris Musées GraphQL API with the provided auth token and query.

        Parameters:
            auth_token (str): Your API token from the Paris Musées account.
            graphql_query (str): A string containing your GraphQL query.

        Returns:
            dict: Parsed JSON response from the API.
        """
        url = "https://apicollections.parismusees.paris.fr/graphql"

        headers = {
            "Content-Type": "application/json",
            "auth-token": auth_token
        }

        payload = {
            "query": graphql_query
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        except Exception as err:
            print(f"Other error occurred: {err}")

    my_token = "5fbf03a9-f458-4641-b13d-5f4e70348428"
    graphql_query = '''
    {
        nodeQuery(
            filter: {conditions: [{field: "type", value: "oeuvre"}, {field: "field_oeuvre_lieux_productions.target_id", value: "170441"}]}
            limit: 500
        ) {
            count
            entities {
            entityUuid
            ... on NodeOeuvre {
                title
                absolutePath
                fieldDateAcquisition {
                startYear
                endYear
                }
                fieldDateProduction {
                endYear
                startYear
                }
                fieldDenominations {
                entity {
                    entityLabel
                    entityId
                }
                }
                fieldOeuvreAuteurs {
                entity {
                    fieldAuteurAuteur {
                    entity {
                        entityId
                        entityLabel
                    }
                    }
                }
                }
                fieldOeuvreDescriptionIcono {
                value
                }
                fieldOeuvreDimensions {
                entity {
                    fieldDimensionUnite {
                    entity {
                        entityLabel
                    }
                    }
                    fieldDimensionType {
                    entity {
                        entityLabel
                    }
                    }
                    fieldDimensionValeur
                }
                }
                queryFieldMusee {
                entities {
                    entityLabel
                    entityId
                }
                count
                }
                fieldOeuvreNumInventaire
                fieldOeuvreSiecle {
                entity {
                    entityLabel
                }
                }
                fieldOeuvreEpoquePeriode {
                entity {
                    entityLabel
                }
                }
                fieldOeuvreTypesObjet {
                entity {
                    entityLabel
                }
                }
                queryFieldModaliteAcquisition {
                entities {
                    entityLabel
                    entityId
                }
                }
                queryFieldMateriauxTechnique {
                count
                entities {
                    entityLabel
                    entityId
                }
                }
                queryFieldDonateurs {
                count
                entities {
                    entityId
                    entityLabel
                }
                }
            }
            }
        }
    }
    '''

    result = call_parismusees_api(my_token, graphql_query)
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if result:
        save_entities_to_files(result)
    #print(json.dumps(result, indent=2, ensure_ascii=False))

get_parismusees_json_files()
