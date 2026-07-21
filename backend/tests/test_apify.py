import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.apify_service import (
    scrape_linkedin_jobs,
    scrape_google_jobs,
    scrape_jobs_concurrently,
    _build_keywords,
    _build_work_types,
    _build_resume_keywords,
    _map_country_and_domain,
    _extract_posted_at,
    _is_within_date_range,
)


@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_success():
    """Validar llamado y mapeo correcto del scraper de LinkedIn de Apify."""
    mock_client = MagicMock()

    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="dataset_lnk", status="SUCCEEDED"))
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = [
        {
            "title": "React Engineer",
            "companyName": "Globex",
            "location": "Madrid",
            "jobUrl": "https://linkedin.com/job/1"
        }
    ]
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    result = await scrape_linkedin_jobs(mock_client, "React Madrid", 1)

    assert len(result) == 1
    assert result[0].title == "React Engineer"
    assert result[0].company == "Globex"
    assert result[0].link == "https://linkedin.com/job/1"

    mock_client.actor.assert_called_once_with("cheap_scraper/linkedin-job-scraper")
    mock_actor.call.assert_called_once()


@pytest.mark.asyncio
async def test_scrape_jobs_concurrently_success():
    """Validar ejecución en paralelo y eliminación de duplicados por URL."""
    mock_lnk_jobs = [
        MagicMock(link="https://job1.com", title="Job 1"),
        MagicMock(link="https://job2.com", title="Job 2")
    ]
    mock_goog_jobs = [
        MagicMock(link="https://job2.com", title="Job 2 duplicate"),
        MagicMock(link="https://job3.com", title="Job 3")
    ]

    with patch("src.services.apify_service.scrape_linkedin_jobs", return_value=mock_lnk_jobs) as mock_lnk:
        with patch("src.services.apify_service.scrape_google_jobs", return_value=mock_goog_jobs) as mock_goog:
            with patch.dict("os.environ", {"APIFY_TOKEN": "dummy_token"}):
                result = await scrape_jobs_concurrently("test query", 5)

                assert len(result) == 3
                links = [j.link for j in result]
                assert "https://job1.com" in links
                assert "https://job2.com" in links
                assert "https://job3.com" in links
                mock_lnk.assert_called_once()
                mock_goog.assert_called_once()


@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_filters():
    """Validar que los filtros nativos del actor se construyan correctamente."""
    mock_client = MagicMock()
    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="dataset_lnk", status="SUCCEEDED"))
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = []
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    await scrape_linkedin_jobs(
        client=mock_client,
        query="Python",
        limit=5,
        location_type="local",
        date_posted="24h",
        target_location="Spain",
        workplace_types="presencial,hibrido",
        resume_skills=["Python", "Docker", "python", ""],
        target_roles=["Python Developer", "Backend Developer"],
    )

    call_args = mock_actor.call.call_args
    run_input = call_args[1]["run_input"]

    assert run_input["keyword"] == ["Python Developer", "Backend Developer"]
    assert run_input["publishedAt"] == "r86400"
    assert run_input["locations"] == ["Spain"]
    assert run_input["workType"] == ["on-site", "hybrid"]
    assert run_input["resumeKeywords"] == [
        {"keyword": "Python"},
        {"keyword": "Docker"},
    ]
    assert "startUrls" not in run_input


@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_remote_filter():
    """Validar que location_type='remote' aplique workType=['remote']."""
    mock_client = MagicMock()
    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="ds", status="SUCCEEDED"))
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = []
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    await scrape_linkedin_jobs(
        client=mock_client,
        query="Developer",
        limit=5,
        location_type="remote",
        target_location="Dominican Republic",
    )

    call_args = mock_actor.call.call_args
    run_input = call_args[1]["run_input"]
    assert run_input["workType"] == ["remote"]
    assert run_input["locations"] == ["Dominican Republic"]


@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_any_date():
    """Validar que date_posted='any' no añada publishedAt."""
    mock_client = MagicMock()
    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="ds", status="SUCCEEDED"))
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = []
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    await scrape_linkedin_jobs(
        client=mock_client,
        query="Developer",
        limit=5,
        date_posted="any",
    )

    call_args = mock_actor.call.call_args
    run_input = call_args[1]["run_input"]
    assert "publishedAt" not in run_input


@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_all_workplace_types():
    """Validar que seleccionar las 3 modalidades envíe las 3 al actor."""
    mock_client = MagicMock()
    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="ds", status="SUCCEEDED"))
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = []
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    await scrape_linkedin_jobs(
        client=mock_client,
        query="Developer",
        limit=5,
        location_type="local",
        workplace_types="presencial,remoto,hibrido",
        target_location="Dominican Republic",
    )

    call_args = mock_actor.call.call_args
    run_input = call_args[1]["run_input"]
    assert run_input["workType"] == ["on-site", "remote", "hybrid"]
    assert run_input["locations"] == ["Dominican Republic"]


def test_build_keywords_with_roles():
    """Target roles deben usarse como keywords."""
    result = _build_keywords("remote python", ["Full Stack Dev", "Backend Engineer"])
    assert result == ["Full Stack Dev", "Backend Engineer"]


def test_build_keywords_translation_es():
    """Roles deben traducirse a español si el idioma es 'es'."""
    result = _build_keywords("remote python", ["Full-Stack Developer", "Frontend Developer"], job_language="es")
    assert result == ["Desarrollador Full Stack", "Desarrollador Frontend"]


def test_build_keywords_strips_work_mode():
    """Palabras de modalidad deben ser removidas del query."""
    result = _build_keywords("React developer remote hibrido", None)
    assert len(result) == 1
    assert "remote" not in result[0].lower()
    assert "hibrido" not in result[0].lower()
    assert "React" in result[0]


def test_build_work_types():
    """Mapeo correcto de modalidades a valores del actor."""
    assert _build_work_types("remote", None) == ["remote"]
    assert _build_work_types("local", "presencial,remoto") == ["on-site", "remote"]
    assert _build_work_types("local", "hibrido") == ["hybrid"]
    assert _build_work_types("both", "") == []
    assert _build_work_types("both", None) == []


def test_build_resume_keywords_dedup():
    """Skills deben ser deduplicados (case-insensitive) y sin vacíos."""
    result = _build_resume_keywords(["Python", "python", "Docker", "", "docker"])
    assert result == [{"keyword": "Python"}, {"keyword": "Docker"}]


@pytest.mark.asyncio
async def test_scrape_google_jobs_success():
    """Validar llamado y mapeo correcto del scraper de Google de Apify."""
    mock_client = MagicMock()

    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="dataset_goog", status="SUCCEEDED"))
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = [
        {
            "title": "Desarrollador de Datos",
            "company_name": "Acme Corp",
            "location": "Remote",
            "apply_options": [
                {"title": "LinkedIn", "link": "https://linkedin.com/job/goog1"},
                {"title": "Company Site", "link": "https://careers.acme.com/goog1"}
            ],
            "description": "Requisitos para el trabajo de datos.",
            "detected_extensions": {"posted_at": "hace 2 horas"}
        }
    ]
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    result = await scrape_google_jobs(
        client=mock_client,
        query="Data Engineer",
        limit=1,
        location_type="remote",
        date_posted="24h",
        target_location="Spain",
        job_language="es"
    )

    assert len(result) == 1
    assert result[0].title == "Desarrollador de Datos"
    assert result[0].company == "Acme Corp"
    assert result[0].link == "https://linkedin.com/job/goog1"
    assert result[0].location == "Remote"

    mock_client.actor.assert_called_once_with("johnvc/google-jobs-scraper")
    mock_actor.call.assert_called_once()
    
    call_args = mock_actor.call.call_args
    run_input = call_args[1]["run_input"]
    assert run_input["query"] == '"Data Ingeniero"'
    assert run_input["country"] == "None"
    assert run_input["google_domain"] == "google.es"
    assert run_input["location"] == "Remote"
    assert "datePosted" not in run_input


def test_map_country_and_domain():
    """Validar mapeo correcto de país y dominio de Google a partir de ubicación/idioma."""
    # Ubicación en España
    country, domain = _map_country_and_domain("Madrid, Spain", "es")
    assert country == "None"
    assert domain == "google.es"

    # Ubicación en México
    country, domain = _map_country_and_domain("Ciudad de México", "es")
    assert country == "mx"
    assert domain == "google.com.mx"

    # Idioma español sin ubicación específica
    country, domain = _map_country_and_domain(None, "es")
    assert country == "None"
    assert domain == "google.es"

    # Por defecto (inglés, EE. UU.)
    country, domain = _map_country_and_domain(None, "en")
    assert country == "us"
    assert domain == "google.com"


def test_extract_posted_at():
    """Validar extracción correcta del texto de fecha de publicación."""
    assert _extract_posted_at({"posted_at": "3 days ago"}) == "3 days ago"
    assert _extract_posted_at({"detected_extensions": {"posted_at": "hace 5 horas"}}) == "hace 5 horas"
    assert _extract_posted_at({"extensions": ["Full-time", "Hace 2 semanas", "USD 3,000"]}) == "Hace 2 semanas"
    assert _extract_posted_at({"extensions": ["Full-time", "USD 3,000"]}) is None


def test_is_within_date_range():
    """Validar filtrado programático de vacantes según su antigüedad."""
    # Filtro 24h
    assert _is_within_date_range("12 hours ago", "24h") is True
    assert _is_within_date_range("hace 5 horas", "24h") is True
    assert _is_within_date_range("1 day ago", "24h") is True
    assert _is_within_date_range("hace 1 día", "24h") is True
    assert _is_within_date_range("2 days ago", "24h") is False
    assert _is_within_date_range("hace 3 días", "24h") is False
    assert _is_within_date_range("Hace 2 semanas", "24h") is False

    # Filtro 7d
    assert _is_within_date_range("5 days ago", "7d") is True
    assert _is_within_date_range("hace 6 días", "7d") is True
    assert _is_within_date_range("Hace 1 semana", "7d") is True
    assert _is_within_date_range("1 week ago", "7d") is True
    assert _is_within_date_range("Hace 2 semanas", "7d") is False
    assert _is_within_date_range("hace 1 mes", "7d") is False

    # Filtro 30d
    assert _is_within_date_range("Hace 3 semanas", "30d") is True
    assert _is_within_date_range("3 weeks ago", "30d") is True
    assert _is_within_date_range("Hace 1 mes", "30d") is True
    assert _is_within_date_range("1 month ago", "30d") is True
    assert _is_within_date_range("Hace 2 meses", "30d") is False
    assert _is_within_date_range("hace 1 año", "30d") is False

    # Sin límite (any)
    assert _is_within_date_range("Hace 3 meses", "any") is True
    assert _is_within_date_range("Hace 3 meses", None) is True

    # None posted_text con filtro activo (la función devuelve True,
    # pero el caller en scrape_google_jobs maneja el None rechazándolo)
    assert _is_within_date_range(None, "24h") is True
    assert _is_within_date_range(None, "any") is True


@pytest.mark.asyncio
async def test_scrape_google_jobs_filters_old_and_unknown_dates():
    """Validar que Google Jobs descarta trabajos viejos o sin fecha cuando filtro activo."""
    mock_client = MagicMock()
    mock_actor = MagicMock()
    mock_run = MagicMock()
    mock_run.status = "SUCCEEDED"
    mock_run.default_dataset_id = "ds789"
    mock_actor.call = AsyncMock(return_value=mock_run)
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = [
        {
            "title": "Trabajo Reciente",
            "company_name": "Empresa A",
            "location": "Remote",
            "apply_options": [{"title": "Web", "link": "https://example.com/job1"}],
            "description": "Un trabajo de programación reciente.",
            "detected_extensions": {"posted_at": "hace 3 horas"}
        },
        {
            "title": "Trabajo Viejo",
            "company_name": "Empresa B",
            "location": "Remote",
            "apply_options": [{"title": "Web", "link": "https://example.com/job2"}],
            "description": "Un trabajo de programación viejo.",
            "detected_extensions": {"posted_at": "Hace 2 semanas"}
        },
        {
            "title": "Trabajo Sin Fecha",
            "company_name": "Empresa C",
            "location": "Remote",
            "apply_options": [{"title": "Web", "link": "https://example.com/job3"}],
            "description": "Un trabajo de programación sin fecha."
        }
    ]
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    result = await scrape_google_jobs(
        client=mock_client,
        query="Programador",
        limit=10,
        location_type="remote",
        date_posted="24h",
        target_location="Remote",
        job_language="es"
    )

    # Solo debe pasar "Trabajo Reciente" (3 horas); el viejo y sin fecha se descartan
    assert len(result) == 1
    assert result[0].title == "Trabajo Reciente"
