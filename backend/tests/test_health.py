from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.db.session import get_db

client = TestClient(app)

def test_health_check_db_connected():
    # Mock database session executing SELECT 1 successfully
    mock_db = MagicMock()
    mock_db.execute.return_value = True

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "connected"
    }

    app.dependency_overrides.clear()
