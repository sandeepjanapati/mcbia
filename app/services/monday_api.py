import requests
from app.config import Config


class MondayClient:
    def __init__(self):
        self.headers = {
            "Authorization": Config.MONDAY_API_KEY,
            "API-Version": Config.MONDAY_API_VERSION,
            "Content-Type": "application/json",
        }

    def _execute_query(self, query):
        try:
            response = requests.post(
                url=Config.MONDAY_URL,
                headers=self.headers,
                json={"query": query},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                print(f"❌ Monday API Error: {data['errors']}")
                return None
            return data
        except requests.exceptions.Timeout:
            print("❌ Monday API request timed out")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"❌ Monday HTTP Error: {e}")
            return None
        except Exception as e:
            print(f"❌ Network Error: {e}")
            return None

    def get_column_mapping(self, board_id):
        query = f'query {{ boards (ids: [{board_id}]) {{ columns {{ title id }} }} }}'
        data = self._execute_query(query)
        if not data:
            return {}
        try:
            cols = data["data"]["boards"][0]["columns"]
            return {c["title"]: c["id"] for c in cols}
        except (IndexError, KeyError):
            return {}

    def fetch_all_items(self, board_id, mapping_dict):
        id_to_name = {v: k for k, v in mapping_dict.items()}
        all_items = []
        cursor = None

        while True:
            cursor_param = "null" if cursor is None else f'"{cursor}"'
            query = f"""
            query {{
              boards (ids: [{board_id}]) {{
                items_page (limit: 500, cursor: {cursor_param}) {{
                  cursor
                  items {{ id name column_values {{ id text }} }}
                }}
              }}
            }}
            """
            data = self._execute_query(query)
            if not data:
                break

            try:
                page_data = data["data"]["boards"][0]["items_page"]
                items = page_data["items"]
                cursor = page_data["cursor"]
            except (IndexError, KeyError):
                break

            for item in items:
                row = {"Item ID": item["id"], "Name": item["name"]}
                for cv in item["column_values"]:
                    if cv["id"] in id_to_name:
                        row[id_to_name[cv["id"]]] = cv["text"]
                all_items.append(row)

            if not cursor:
                break

        return all_items