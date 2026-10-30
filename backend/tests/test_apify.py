import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.apify_service import (
    scrape_linkedin_jobs,
    scrape_google_jobs,
    scrape_jobs_concurrently,
    _build_keywords,
    _build_workplace_params,
    _map_country,
    COUNTRY_KEYWORDS,
    _role_tokens,
    _ts_relevant_title,
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
            "url": "https://linkedin.com/job/1"
        }
    ]
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    result = await scrape_linkedin_jobs(mock_client, "React Madrid", 1)

    assert len(result) == 1
    assert result[0].title == "React Engineer"
    assert result[0].company == "Globex"
    assert result[0].link == "https://linkedin.com/job/1"

    mock_client.actor.assert_called_once_with("valig/linkedin-jobs-scraper")
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
    """Validar que los filtros del actor se construyan correctamente (un run por rol)."""
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

    run_inputs = [c.kwargs["run_input"] for c in mock_actor.call.call_args_list]
    assert [r["keywords"] for r in run_inputs] == ["Python Developer", "Backend Developer"]

    for run_input in run_inputs:
        assert run_input["datePosted"] == "r86400"
        assert run_input["location"] == "Spain"
        assert run_input["urlParam"] == [{"key": "f_WT", "value": "1,3"}]
        assert run_input["limit"] == 25
        assert "resumeKeywords" not in run_input
        assert "workType" not in run_input
        assert "startUrls" not in run_input


@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_remote_filter():
    """Validar que location_type='remote' envíe f_WT=2."""
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
    assert run_input["urlParam"] == [{"key": "f_WT", "value": "2"}]
    assert run_input["location"] == "Dominican Republic"


@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_any_date():
    """Validar que date_posted='any' no añada datePosted."""
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
    assert "datePosted" not in run_input


@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_all_workplace_types():
    """Validar que seleccionar las 3 modalidades envíe los 3 códigos f_WT."""
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
    assert run_input["urlParam"] == [{"key": "f_WT", "value": "1,2,3"}]
    assert run_input["location"] == "Dominican Republic"


@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_dedupes_across_roles():
    """Dos búsquedas de rol que devuelven la misma vacante no deben duplicarla."""
    mock_client = MagicMock()
    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="ds", status="SUCCEEDED"))
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = [
        {"title": "React Developer", "companyName": "A", "url": "https://linkedin.com/job/1"},
        {"title": "React Developer", "companyName": "B", "url": "https://linkedin.com/job/2"},
    ]
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    result = await scrape_linkedin_jobs(
        client=mock_client,
        query="Developer",
        limit=10,
        target_roles=["Frontend Developer", "Backend Developer"],
    )

    links = [j.link for j in result]
    assert links == ["https://linkedin.com/job/1", "https://linkedin.com/job/2"]
    assert mock_actor.call.call_count == 2


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


def test_build_workplace_params():
    """Mapeo correcto de modalidades al parámetro f_WT de LinkedIn."""
    assert _build_workplace_params("remote", None) == [{"key": "f_WT", "value": "2"}]
    assert _build_workplace_params("local", "presencial,remoto") == [{"key": "f_WT", "value": "1,2"}]
    assert _build_workplace_params("local", "hibrido") == [{"key": "f_WT", "value": "3"}]
    assert _build_workplace_params("both", "") == []
    assert _build_workplace_params("both", None) == []


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
            "company": "Acme Corp",
            "location": "Madrid, Spain",
            "isRemote": False,
            "postedAt": "2026-10-20",
            "ageDays": 0,
            "applyUrl": "https://linkedin.com/job/goog1",
            "applyOptions": [
                {"source": "LinkedIn", "url": "https://linkedin.com/job/goog1"},
                {"source": "Company Site", "url": "https://careers.acme.com/goog1"}
            ],
            "description": "Requisitos para el trabajo de datos."
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
    assert result[0].location == "Madrid, Spain"
    assert result[0].date_posted_unknown is False

    mock_client.actor.assert_called_once_with("inovaflow/google-jobs-scraper")
    mock_actor.call.assert_called_once()

    call_args = mock_actor.call.call_args
    run_input = call_args[1]["run_input"]
    assert run_input["queries"] == ["Data Ingeniero"]
    assert run_input["country"] == "es"
    assert run_input["locations"] == ["Spain"]
    assert run_input["postedWithin"] == "day"
    assert run_input["remoteOnly"] is True
    assert run_input["maxJobsPerQuery"] == 25
    assert run_input["language"] == "es"
    assert run_input["maxApplyOptions"] == 1
    # Params de otros actores no deben enviarse
    assert "countryCode" not in run_input
    assert "datePosted" not in run_input


def test_map_country():
    """Validar mapeo del país (edición de Google) a partir de ubicación/idioma."""
    assert _map_country("Madrid, Spain", "es") == "es"
    assert _map_country("Ciudad de México", "es") == "mx"
    assert _map_country("Bogotá, Colombia", "es") == "co"
    assert _map_country("London, UK", "en") == "gb"
    assert _map_country(None, "es") == "es"
    assert _map_country(None, "en") == "us"
    # "Ukraine" no debe confundirse con el Reino Unido
    assert _map_country("Kyiv, Ukraine", "en") == "us"
    # "India" no debe coincidir con "Indiana"
    assert _map_country("Indianapolis, Indiana", "en") == "us"
    # "New Mexico" no debe coincidir con México
    assert _map_country("New Mexico, USA", "en") == "us"
    # "Northern Ireland" es Reino Unido, no Irlanda
    assert _map_country("Belfast, Northern Ireland", "en") == "gb"
    assert _map_country("Dublin, Ireland", "en") == "ie"
    # Cobertura de las 47 ediciones: ciudades que antes caían al fallback
    assert _map_country("Lisbon, Portugal", "en") == "pt"
    assert _map_country("Amsterdam, Netherlands", "en") == "nl"
    assert _map_country("Dubai, UAE", "en") == "ae"
    assert _map_country("Buenos Aires, Argentina", "es") == "ar"
    assert _map_country("Santiago, Chile", "es") == "cl"
    assert _map_country("Seoul, South Korea", "en") == "kr"
    assert _map_country("Munich, Germany", "en") == "de"
    assert _map_country("Milan, Italy", "en") == "it"
    assert _map_country("Auckland, New Zealand", "en") == "nz"
    assert _map_country("Santiago, Dominican Republic", "es") == "es"


def test_country_keywords_cover_all_google_editions():
    """COUNTRY_KEYWORDS debe cubrir exactamente las 47 ediciones del actor."""
    expected = {
        "us", "gb", "ca", "au", "ie", "nz", "in", "sg", "za", "ae", "de", "fr",
        "nl", "be", "ch", "at", "es", "it", "pt", "se", "no", "dk", "fi", "pl",
        "cz", "hu", "ro", "gr", "tr", "br", "mx", "ar", "cl", "co", "jp", "kr",
        "hk", "tw", "ph", "my", "id", "th", "vn", "il", "ng", "ke", "eg",
    }
    assert {code for _, code in COUNTRY_KEYWORDS} == expected
    assert len(COUNTRY_KEYWORDS) == 47


@pytest.mark.asyncio
async def test_scrape_google_jobs_marks_unknown_date():
    """El actor filtra la fecha; solo se marca date_posted_unknown si el item no trae edad."""
    mock_client = MagicMock()
    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="ds789", status="SUCCEEDED"))
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = [
        {
            "title": "Trabajo Reciente",
            "company": "Empresa A",
            "location": "Remote",
            "applyUrl": "https://example.com/job1",
            "description": "Un trabajo de programación reciente.",
            "postedAt": "2026-10-21",
            "ageDays": 0
        },
        {
            "title": "Trabajo Sin Fecha",
            "company": "Empresa C",
            "location": "Remote",
            "applyOptions": [{"source": "Web", "url": "https://example.com/job3"}],
            "description": "Un trabajo de programación sin fecha."
        }
    ]
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    result = await scrape_google_jobs(
        client=mock_client,
        query="Programador",
        limit=10,
        date_posted="24h",
        target_location="Remote",
        job_language="es"
    )

    by_title = {j.title: j for j in result}
    assert set(by_title) == {"Trabajo Reciente", "Trabajo Sin Fecha"}
    assert by_title["Trabajo Reciente"].date_posted_unknown is False
    assert by_title["Trabajo Sin Fecha"].date_posted_unknown is True
    # applyOptions se usa como fallback cuando falta applyUrl
    assert by_title["Trabajo Sin Fecha"].link == "https://example.com/job3"

    run_input = mock_actor.call.call_args[1]["run_input"]
    assert run_input["postedWithin"] == "day"


@pytest.mark.asyncio
async def test_scrape_google_jobs_any_date_omits_posted_within():
    """Sin filtro de fecha no se envía postedWithin ni remoteOnly."""
    mock_client = MagicMock()
    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="ds", status="SUCCEEDED"))
    mock_client.actor.return_value = mock_actor

    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = []
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset

    await scrape_google_jobs(
        client=mock_client,
        query="Developer",
        limit=5,
        location_type="local",
        date_posted="any",
        workplace_types="presencial",
        target_location="Spain"
    )

    run_input = mock_actor.call.call_args[1]["run_input"]
    assert "postedWithin" not in run_input
    assert "remoteOnly" not in run_input
    assert run_input["locations"] == ["Spain"]


def test_title_relevance_filter():
    """Filtro data-driven: título debe solaparse con tokens de target_roles, nunca hardcodeado."""
    roles = ["Full-Stack Developer", "Frontend Developer", "Backend Developer", "Web Developer"]
    tokens = _role_tokens(roles)

    assert "developer" in tokens
    assert "desarrollador" in tokens
    assert "fullstack" in tokens or "full" in tokens

    # Dev jobs keep
    assert _ts_relevant_title("Full Stack Developer Junior", tokens)
    assert _ts_relevant_title("Desarrollador Frontend", tokens)
    assert _ts_relevant_title("Backend Engineer", tokens)

    # Unrelated jobs drop
    assert not _ts_relevant_title("Cajero", tokens)
    assert not _ts_relevant_title("Abogado", tokens)
    assert not _ts_relevant_title("Gerente de Mercadeo", tokens)
    assert not _ts_relevant_title("Community manager", tokens)

    # No roles provided => filter disabled (no orphaned results)
    assert _ts_relevant_title("Cajero", _role_tokens(None))
    assert _ts_relevant_title("Cajero", set())
