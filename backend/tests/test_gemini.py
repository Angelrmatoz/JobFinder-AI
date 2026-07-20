import pytest
from unittest.mock import MagicMock, patch
from src.services.gemini_service import parse_cv_with_gemma, evaluate_job_match, get_client
from src.schemas.cv import CVProfile, JobMatchResult

def test_get_client_error_missing_env():
    """Validar que get_client lance un error si la variable GEMINI_API_KEY no está configurada."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError) as excinfo:
            get_client()
        assert "GEMINI_API_KEY environment variable is not set" in str(excinfo.value)

def test_parse_cv_with_gemma_success(mock_cv_profile):
    """Validar procesamiento del CV simulando la respuesta estructurada de Gemini."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = mock_cv_profile
    mock_client.models.generate_content.return_value = mock_response
    
    with patch("src.services.gemini_service.get_client", return_value=mock_client):
        result = parse_cv_with_gemma("Mi currículum es...")
        
        assert result.name == "Juan Pérez"
        assert "Python" in result.skills
        mock_client.models.generate_content.assert_called_once()

def test_evaluate_job_match_success(mock_cv_profile):
    """Validar evaluación de afinidad simulando la respuesta estructurada de Gemini."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed = JobMatchResult(match_score=9, explanation="Encaja perfectamente con la vacante.")
    mock_client.models.generate_content.return_value = mock_response
    
    with patch("src.services.gemini_service.get_client", return_value=mock_client):
        result = evaluate_job_match(
            mock_cv_profile,
            "Software Developer",
            "Example Corp",
            "Buscamos desarrollador Python"
        )
        
        assert result.match_score == 9
        assert "perfectamente" in result.explanation
        mock_client.models.generate_content.assert_called_once()

def test_evaluate_job_match_language_mismatch_es(mock_cv_profile):
    """Validar que retorne puntuación baja (1) si se pide español y la descripción está en inglés o latín."""
    # Caso 1: Latín / Lorem Ipsum
    latin_desc = "Laoreet vel urna duis vitae tellus velit. Malesuada at malesuada a eu id eu placerat."
    result_latin = evaluate_job_match(mock_cv_profile, "Frontend Developer", "Brain-lab.ai", latin_desc, job_language="es")
    assert result_latin.match_score == 1
    assert "no es Español" in result_latin.explanation

    # Caso 2: Inglés
    english_desc = "We are seeking a Frontend Developer with React and TypeScript experience in Miami."
    result_english = evaluate_job_match(mock_cv_profile, "Frontend Developer", "Brain-lab.ai", english_desc, job_language="es")
    assert result_english.match_score == 1
    assert "no es Español" in result_english.explanation

def test_evaluate_job_match_language_mismatch_en(mock_cv_profile):
    """Validar que retorne puntuación baja (1) si se pide inglés y la descripción está en español."""
    spanish_desc = "Buscamos desarrollador Frontend con experiencia en React y TypeScript en Madrid."
    result = evaluate_job_match(mock_cv_profile, "Frontend Developer", "Brain-lab.ai", spanish_desc, job_language="en")
    assert result.match_score == 1
    assert "not English" in result.explanation
