from cosmosdb._dbutils import _get_container


class Prompts:
    def __init__(self):
        self.container = _get_container("control", "prompts")

    def get_prompt(self, function: str, version: int = None) -> str:
        if not version:
            # get the latest version
            query = f"SELECT * FROM c WHERE c.function = '{function}' ORDER BY c.version DESC"

        else:
            query = f"SELECT * FROM c WHERE c.function = '{function}' AND c.version = {version}"

        records = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )

        # if there are no records, raise an error
        if not records:
            raise ValueError(
                f"No prompt found for function {function} and version {version}"
            )

        # else, get the record with the highest version
        record = records[0]
        prompt = record.get("prompt", None)

        if not prompt or prompt == "":
            raise ValueError(
                f"No prompt found for function {function} and version {version}"
            )

        return prompt
