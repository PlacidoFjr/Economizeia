import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal, Base, engine
from app.db.models import User, Bill, BillStatus
from app.core.security import get_password_hash, create_access_token
import io

client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("test123"),
        name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Get auth token for test user."""
    return create_access_token(data={"sub": str(test_user.id)})


def test_list_bills(auth_token):
    """Test listing bills."""
    response = client.get(
        "/api/v1/bills",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_bill_not_found(auth_token):
    """Test getting non-existent bill."""
    import uuid
    response = client.get(
        f"/api/v1/bills/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


def test_upload_bill(auth_token):
    """Test bill upload."""
    # Create a dummy PDF file
    file_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 0\ntrailer\n<<\n/Root 1 0 R\n>>\nstartxref\n0\n%%EOF"
    
    response = client.post(
        "/api/v1/bills/upload",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("test.pdf", file_content, "application/pdf")}
    )
    
    # Should accept the upload (processing happens async)
    assert response.status_code in [201, 200]
    data = response.json()
    assert "bill_id" in data

