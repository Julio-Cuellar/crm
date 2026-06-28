import json
import os
import sys

# Ensure backend root is in PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

# Generate the OpenAPI schema
openapi_schema = app.openapi()

# Write to backend/openapi.json
output_path = os.path.join(os.path.dirname(__file__), "..", "openapi.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

print(f"SUCCESS: OpenAPI schema successfully exported to {output_path}")
