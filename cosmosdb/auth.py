from ._dbutils import _get_container


class Auth:
    def __init__(self):
        self.container = _get_container("auth", "users")

    def check_user_in_db(self, user: dict) -> bool:
        # Get the sub from the user
        sub = user.get("sub")

        if not sub:
            return False

        # Query to retrieve a specific record
        query = f"SELECT * FROM c WHERE c.sub = '{sub}'"

        # Fetching the record
        items = list(
            self.container.query_items(query=query, enable_cross_partition_query=True)
        )

        if not items:
            return False
        else:
            return True
