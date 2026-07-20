import pytest
from unittest.mock import patch, MagicMock

def test_health_endpoint(client):
    """Validar que el endpoint de salud retorne estado en línea."""
    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "test_key",
        "APIFY_TOKEN": "test_token",
        "NOTION_API_KEY": "test_key",
        "NOTION_DATABASE_ID": "test_db"
    }):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["apis"]["gemini"] is True
        assert data["apis"]["apify"] is True
        assert data["apis"]["notion"] is True

def test_upload_cv_invalid_file_type(client):
    """Validar que subir un archivo que no es PDF retorne error 400."""
    response = client.post(
        "/api/upload-cv",
        files={"file": ("cv.png", b"fake_png_data", "image/png")}
    )
    assert response.status_code == 400
    assert "Solo se admiten archivos PDF." in response.json()["detail"]

@patch("src.routers.jobs.extract_text_from_pdf")
@patch("src.routers.jobs.parse_cv_with_gemma")
@patch("src.routers.jobs.scrape_jobs_concurrently")
@patch("src.routers.jobs.evaluate_job_match")
@patch("src.routers.jobs.save_job_to_notion")
def test_upload_cv_success(
    mock_save_notion,
    mock_eval_match,
    mock_scrape_jobs,
    mock_parse_cv,
    mock_extract_pdf,
    client,
    mock_cv_profile,
    mock_job_detail
):
    """Validar pipeline completo de procesamiento de CV con endpoints exitosos."""
    # Configurar mocks
    mock_extract_pdf.return_value = "Texto extraído del CV"
    mock_parse_cv.return_value = mock_cv_profile
    
    # Retornar una lista con una vacante
    mock_scrape_jobs.return_value = [mock_job_detail]
    
    # Puntuación mayor a 7 para activar guardado en Notion
    from src.schemas.cv import JobMatchResult
    mock_eval_match.return_value = JobMatchResult(match_score=8, explanation="Tip de prueba")
    mock_save_notion.return_value = True

    # Realizar petición
    response = client.post(
        "/api/upload-cv",
        files={"file": ("mi_cv.pdf", b"fake_pdf_data", "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar mapeo de salida
    assert data["profile"]["name"] == "Juan Pérez"
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["title"] == mock_job_detail.title
    assert data["jobs"][0]["match_score"] == 8
    assert data["jobs"][0]["apply_tip"] == "Tip de prueba"
    assert data["jobs"][0]["saved_to_notion"] is True

    # Verificar que los métodos de los servicios fueron llamados
    mock_extract_pdf.assert_called_once()
    mock_parse_cv.assert_called_once_with("Texto extraído del CV", None)
    mock_scrape_jobs.assert_called_once_with(
        query=mock_cv_profile.search_query,
        limit=15,
        location_type=None,
        date_posted="7d",
        target_location=None,
        workplace_types=None,
        resume_skills=mock_cv_profile.skills,
        target_roles=mock_cv_profile.target_roles,
        job_language="both",
    )
    mock_eval_match.assert_called_once()
    mock_save_notion.assert_called_once()

@patch("src.routers.jobs.generate_chat_response")
def test_chat_endpoint_success(mock_generate_chat, client):
    """Validar endpoint de chat de asesor de carrera con mocks."""
    mock_generate_chat.return_value = "Respuesta del Asesor IA"
    
    response = client.post(
        "/api/chat",
        json={"question": "Hola", "context": "{}"}
    )
    
    assert response.status_code == 200
    assert response.json()["answer"] == "Respuesta del Asesor IA"
    mock_generate_chat.assert_called_once()
