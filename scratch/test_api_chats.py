import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.modules.identity.interfaces.api.dependencies.auth_bearer import get_current_user
from app.modules.identity.domain.entities.user import User

# Mocked User with the target tenant ID
mock_user = User(
    id=uuid.UUID("d0e3d233-eb3a-4467-9c92-d6d7cfef5877"),
    tenant_id=uuid.UUID("5ed79324-5b0d-44b5-9ff8-a567eadb8785"),
    email="julio@example.com",
    name="julio cuellar",
    role="OWNER",
    password_hash="some_hashed_password"
)


async def mock_get_current_user():
    return mock_user


app.dependency_overrides[get_current_user] = mock_get_current_user


def run_test():
    with TestClient(app) as client:
        response = client.get("/api/v1/chats")
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        import json
        print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    run_test()
