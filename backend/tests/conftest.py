import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.database import get_db, Base
from api.auth import get_current_user
from models.user import User
from models.organization import Organization

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Set up test database with all tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    organization = Organization(
        name="Test Organization",
        slug="test-org",
        description="Test organization for testing",
        settings={},
        is_active=True
    )
    db_session.add(organization)
    await db_session.commit()
    await db_session.refresh(organization)
    return organization


@pytest.fixture
async def test_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        organization_id=test_organization.id,
        role="admin",
        is_active=True
    )
    user.set_password("testpassword123")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_readonly(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create a test user with readonly permissions."""
    user = User(
        email="readonly@example.com",
        username="readonlyuser",
        full_name="Readonly User",
        organization_id=test_organization.id,
        role="readonly",
        is_active=True
    )
    user.set_password("testpassword123")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override the database dependency."""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_get_current_user(test_user: User):
    """Override the current user dependency."""
    async def _override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db, override_get_current_user) -> TestClient:
    """Create a test client with overridden dependencies."""
    return TestClient(app)


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Get authentication headers for the test user."""
    # In a real implementation, you would generate a JWT token here
    # For testing, we'll use a mock token
    return {"Authorization": f"Bearer test_token_{test_user.id}"}


@pytest.fixture
def readonly_auth_headers(test_user_readonly: User) -> dict:
    """Get authentication headers for the readonly test user."""
    return {"Authorization": f"Bearer test_token_{test_user_readonly.id}"}


# Test data fixtures
@pytest.fixture
def sample_feature_data():
    """Sample feature data for testing."""
    return {
        "name": "user_age",
        "description": "User age in years",
        "data_type": "integer",
        "feature_type": "numeric",
        "entity_type": "user",
        "serving_mode": "online",
        "storage_type": "postgresql",
        "tags": ["demographic", "user"],
        "metadata": {
            "min_value": 0,
            "max_value": 120,
            "default_value": None
        }
    }


@pytest.fixture
def sample_feature_value_data():
    """Sample feature value data for testing."""
    return {
        "feature_id": 1,
        "entity_id": "user_123",
        "value": 25,
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {
            "source": "user_profile",
            "confidence": 0.95
        }
    }


@pytest.fixture
def sample_data_quality_metric_data():
    """Sample data quality metric data for testing."""
    return {
        "feature_id": 1,
        "metric_type": "completeness",
        "value": 95.5,
        "threshold": 90.0,
        "status": "active",
        "metadata": {
            "null_count": 45,
            "total_count": 1000
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_performance_metric_data():
    """Sample performance metric data for testing."""
    return {
        "service_name": "feature_serving",
        "metric_name": "latency_p95",
        "value": 150.5,
        "unit": "ms",
        "labels": {
            "endpoint": "/api/feature-values/serve",
            "method": "POST"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_alert_data():
    """Sample alert data for testing."""
    return {
        "title": "High Data Quality Alert",
        "description": "Data quality score dropped below threshold",
        "severity": "warning",
        "source": "data_quality_monitor",
        "metadata": {
            "feature_id": 1,
            "metric_type": "completeness",
            "current_value": 85.0,
            "threshold": 90.0
        },
        "status": "active"
    }


@pytest.fixture
def sample_computation_job_data():
    """Sample computation job data for testing."""
    return {
        "name": "daily_feature_aggregation",
        "description": "Daily aggregation of user features",
        "job_type": "aggregation",
        "config": {
            "features": ["user_age", "user_income"],
            "aggregation_functions": ["mean", "std", "count"],
            "time_window": "24h"
        },
        "schedule": {
            "type": "daily",
            "time": "02:00:00"
        }
    }


# Utility functions for testing
def create_test_feature(db_session: AsyncSession, organization_id: int, **kwargs):
    """Helper function to create a test feature."""
    from models.feature import Feature
    
    feature_data = {
        "name": "test_feature",
        "description": "Test feature for testing",
        "data_type": "string",
        "feature_type": "categorical",
        "entity_type": "user",
        "serving_mode": "online",
        "storage_type": "postgresql",
        "tags": ["test"],
        "metadata": {},
        "organization_id": organization_id,
        **kwargs
    }
    
    feature = Feature(**feature_data)
    db_session.add(feature)
    return feature


def create_test_feature_value(db_session: AsyncSession, feature_id: int, organization_id: int, **kwargs):
    """Helper function to create a test feature value."""
    from models.feature import FeatureValue
    
    value_data = {
        "feature_id": feature_id,
        "entity_id": "test_entity",
        "value": "test_value",
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {},
        "organization_id": organization_id,
        **kwargs
    }
    
    feature_value = FeatureValue(**value_data)
    db_session.add(feature_value)
    return feature_value


# Async test utilities
async def create_test_data(db_session: AsyncSession, test_organization: Organization, test_user: User):
    """Create comprehensive test data for integration tests."""
    from models.feature import Feature, FeatureValue
    from models.monitoring import DataQualityMetric, PerformanceMetric, Alert
    from models.computation import ComputationJob
    
    # Create test features
    feature1 = Feature(
        name="user_age",
        description="User age in years",
        data_type="integer",
        feature_type="numeric",
        entity_type="user",
        serving_mode="online",
        storage_type="postgresql",
        tags=["demographic"],
        metadata={},
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    
    feature2 = Feature(
        name="user_income",
        description="User income in USD",
        data_type="float",
        feature_type="numeric",
        entity_type="user",
        serving_mode="online",
        storage_type="postgresql",
        tags=["financial"],
        metadata={},
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    
    db_session.add_all([feature1, feature2])
    await db_session.commit()
    await db_session.refresh(feature1)
    await db_session.refresh(feature2)
    
    # Create test feature values
    value1 = FeatureValue(
        feature_id=feature1.id,
        entity_id="user_123",
        value=25,
        timestamp="2024-01-01T00:00:00Z",
        metadata={},
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    
    value2 = FeatureValue(
        feature_id=feature2.id,
        entity_id="user_123",
        value=50000.0,
        timestamp="2024-01-01T00:00:00Z",
        metadata={},
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    
    db_session.add_all([value1, value2])
    await db_session.commit()
    
    # Create test monitoring data
    quality_metric = DataQualityMetric(
        feature_id=feature1.id,
        metric_type="completeness",
        value=95.5,
        threshold=90.0,
        status="active",
        metadata={},
        timestamp="2024-01-01T00:00:00Z",
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    
    performance_metric = PerformanceMetric(
        service_name="feature_serving",
        metric_name="latency_p95",
        value=150.5,
        unit="ms",
        labels={},
        timestamp="2024-01-01T00:00:00Z",
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    
    alert = Alert(
        title="Test Alert",
        description="Test alert for testing",
        severity="warning",
        source="test",
        metadata={},
        status="active",
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    
    db_session.add_all([quality_metric, performance_metric, alert])
    await db_session.commit()
    
    # Create test computation job
    job = ComputationJob(
        name="test_job",
        description="Test computation job",
        job_type="aggregation",
        config={},
        schedule={},
        status="pending",
        organization_id=test_organization.id,
        created_by=test_user.id
    )
    
    db_session.add(job)
    await db_session.commit()
    
    return {
        "features": [feature1, feature2],
        "values": [value1, value2],
        "quality_metrics": [quality_metric],
        "performance_metrics": [performance_metric],
        "alerts": [alert],
        "jobs": [job]
    } 