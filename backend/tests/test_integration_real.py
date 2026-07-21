import pytest
import os
import time
from src.services.gemini_service import parse_cv_with_gemma, evaluate_job_match
from src.services.notion_service import save_job_to_notion
from src.schemas.cv import JobDetail

@pytest.mark.integration
def test_gemini_integration_real():
    """Prueba de integración real con el API de Gemini (Google AI Studio)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        pytest.skip("OMITIDO: GEMINI_API_KEY real no configurada en el entorno.")
        
    cv_text = "Ángel Matos. Desarrollador React Junior y NodeJS. 1 año de experiencia."
    
    # 4 segundos de retardo para protección de Rate Limit (15 RPM)
    time.sleep(4)
    
    profile = parse_cv_with_gemma(cv_text)
    
    assert profile.skills is not None
    assert len(profile.skills) > 0
    assert profile.search_query is not None

@pytest.mark.integration
def test_notion_integration_real():
    """Prueba de integración real con el API de Notion (insertar registro de prueba)."""
    token = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_DATABASE_ID")
    
    if not token or token == "your_notion_api_key_here" or not db_id or db_id == "your_notion_database_id_here":
        pytest.skip("OMITIDO: NOTION_API_KEY o NOTION_DATABASE_ID reales no configuradas.")
        
    dummy_job = JobDetail(
        title="Integration Test Vacancy",
        company="JobFinder AI Tests",
        location="Internet",
        link="https://notion.so",
        description="Esta es una vacante de prueba generada automáticamente por tests automatizados.",
        match_score=9,
        apply_tip="Prueba exitosa. No aplicar.",
        saved_to_notion=False
    )
    
    # Pausa de seguridad
    time.sleep(4)
    
    result = save_job_to_notion(dummy_job)
    assert result is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_apify_integration_real():
    """Prueba de integración real con el API de Apify (Scraping concurrente)."""
    token = os.getenv("APIFY_TOKEN")
    if not token or token == "your_apify_token_here":
        pytest.skip("OMITIDO: APIFY_TOKEN real no configurado en el entorno.")

    from src.services.apify_service import scrape_jobs_concurrently

    # Realizar consulta básica rápida
    jobs = await scrape_jobs_concurrently(
        query="React Developer",
        limit=1,
        date_posted="24h",
        job_language="es"
    )

    assert isinstance(jobs, list)
