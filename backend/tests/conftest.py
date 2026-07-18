import sys
import os
import pytest
from fastapi.testclient import TestClient

# Añadir el directorio 'backend' al PYTHONPATH para que reconozca el módulo 'src'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from src.schemas.cv import CVProfile, JobDetail, JobMatchResult

def pytest_addoption(parser):
    """Agregar opción --run-integration por línea de comando."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run real integration tests requiring real API credentials"
    )

def pytest_configure(config):
    """Registrar marcador personalizado 'integration'."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test with real APIs"
    )

def pytest_collection_modifyitems(config, items):
    """Omitir pruebas de integración a menos que se use el flag --run-integration."""
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(reason="Necesita opción --run-integration para ejecutarse")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)

@pytest.fixture
def client():
    """Fixture para obtener cliente de pruebas de FastAPI."""
    return TestClient(app)

@pytest.fixture
def mock_cv_profile():
    """Fixture con perfil mock de prueba."""
    return CVProfile(
        name="Juan Pérez",
        email="juan.perez@example.com",
        skills=["Python", "React", "Docker", "SQL"],
        experience_summary="Desarrollador Full Stack con 3 años de experiencia en desarrollo web.",
        target_roles=["Full Stack Developer", "Backend Engineer"],
        search_query="React Python Developer remote"
    )

@pytest.fixture
def mock_job_detail():
    """Fixture con detalle de vacante mock de prueba."""
    return JobDetail(
        title="Software Engineer (Python/React)",
        company="Tech Solutions S.A.",
        location="Remote (LATAM)",
        link="https://example.com/job/123",
        description="Buscamos desarrollador con conocimientos en Python, FastAPI y React.",
        match_score=8,
        apply_tip="Destaca tus proyectos en FastAPI y despliegues con Docker.",
        saved_to_notion=False
    )
