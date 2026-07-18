import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.apify_service import scrape_linkedin_jobs, scrape_google_jobs, scrape_jobs_concurrently

@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_success():
    """Validar llamado y mapeo correcto del scraper de LinkedIn de Apify."""
    mock_client = MagicMock()
    
    # Mock del actor call (async)
    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="dataset_lnk"))
    mock_client.actor.return_value = mock_actor
    
    # Mock del dataset list_items (async)
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
async def test_scrape_google_jobs_success():
    """Validar llamado y mapeo correcto del scraper de Google Jobs de Apify."""
    mock_client = MagicMock()
    
    # Mock actor call
    mock_actor = MagicMock()
    mock_actor.call = AsyncMock(return_value=MagicMock(default_dataset_id="dataset_ggl"))
    mock_client.actor.return_value = mock_actor
    
    # Mock dataset list_items
    mock_dataset = MagicMock()
    mock_dataset_items = MagicMock()
    mock_dataset_items.items = [
        {
            "title": "Python Developer",
            "companyName": "ACME",
            "location": "Remote",
            "applyLink": "https://google.com/job/2"
        }
    ]
    mock_dataset.list_items = AsyncMock(return_value=mock_dataset_items)
    mock_client.dataset.return_value = mock_dataset
    
    result = await scrape_google_jobs(mock_client, "Python Remote", 1)
    
    assert len(result) == 1
    assert result[0].title == "Python Developer"
    assert result[0].company == "ACME"
    assert result[0].link == "https://google.com/job/2"
    
    mock_client.actor.assert_called_once_with("orgupdate/google-jobs-scraper")
    mock_actor.call.assert_called_once()

@pytest.mark.asyncio
async def test_scrape_jobs_concurrently_success():
    """Validar ejecución en paralelo y eliminación de duplicados por URL."""
    # Simular retornos de las funciones internas
    mock_lnk_jobs = [
        MagicMock(link="https://job1.com", title="Job 1"),
        MagicMock(link="https://job2.com", title="Job 2")
    ]
    mock_ggl_jobs = [
        # Job 2 es duplicado (mismo link)
        MagicMock(link="https://job2.com", title="Job 2 Duplicated"),
        MagicMock(link="https://job3.com", title="Job 3")
    ]
    
    with patch("src.services.apify_service.scrape_linkedin_jobs", return_value=mock_lnk_jobs) as mock_lnk:
        with patch.dict("os.environ", {"APIFY_TOKEN": "dummy_token"}):
            result = await scrape_jobs_concurrently("test query", 5)
            
            # Deben quedar exactamente 2 vacantes únicas porque Google Jobs se deshabilitó
            assert len(result) == 2
            links = [j.link for j in result]
            assert "https://job1.com" in links
            assert "https://job2.com" in links
            
            mock_lnk.assert_called_once()
