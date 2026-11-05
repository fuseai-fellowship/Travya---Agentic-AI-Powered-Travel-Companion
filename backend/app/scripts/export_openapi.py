"""Print the OpenAPI document (used to regenerate the typed frontend client)."""

import json

from app.main import create_app

if __name__ == "__main__":
    print(json.dumps(create_app().openapi(), indent=2))
