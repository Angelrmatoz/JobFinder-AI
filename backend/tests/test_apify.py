import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.apify_service import (
    scrape_linkedin_jobs,
    scrape_jobs_concurrently,
    _build_keywords,
    _build_work_types,
    _build_resume_keywords,
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

    with patch("src.services.apify_service.scrape_linkedin_jobs", return_value=mock_lnk_jobs) as mock_lnk:
        with patch.dict("os.environ", {"APIFY_TOKEN": "dummy_token"}):
            result = await scrape_jobs_concurrently("test query", 5)

            assert len(result) == 2
            links = [j.link for j in result]
            assert "https://job1.com" in links
            assert "https://job2.com" in links
            mock_lnk.assert_called_once()


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
