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


def test_generate_chat_response_success():
    """Validar que generate_chat_response llama al fallback chain y retorna texto."""
    from src.services.gemini_service import generate_chat_response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Asesor responde con consejos."
    mock_client.models.generate_content.return_value = mock_response

    with patch("src.services.gemini_service.get_client", return_value=mock_client):
        result = generate_chat_response("Dame consejos para mejorar mi CV.")

    assert result == "Asesor responde con consejos."
    mock_client.models.generate_content.assert_called_once()


def test_generate_content_with_fallback_first_model_succeeds():
    """Validar que fallback chain retorna respuesta del primer modelo si no falla."""
    from src.services.gemini_service import generate_content_with_fallback
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict("os.environ", {"GEMINI_API_KEY": "key", "GEMINI_MODEL": "model-1"}):
        result = generate_content_with_fallback(mock_client, "prompt", config=None)

    assert result is mock_response
    assert mock_client.models.generate_content.call_count == 1


def test_generate_content_with_fallback_uses_second_on_first_failure():
    """Validar que fallback chain pasa al segundo modelo si el primero falla."""
    from src.services.gemini_service import generate_content_with_fallback
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_client.models.generate_content.side_effect = [
        RuntimeError("model-1 error"),
        mock_response,
    ]

    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "key",
        "GEMINI_MODEL": "model-1",
        "GEMINI_MODEL_FALLBACK_1": "model-2",
        "GEMINI_MODEL_FALLBACK_2": "model-3",
    }):
        result = generate_content_with_fallback(mock_client, "prompt", config=None)

    assert result is mock_response
    assert mock_client.models.generate_content.call_count == 2


def test_generate_content_with_fallback_raises_when_all_fail():
    """Validar que fallback chain lanza RuntimeError si todos los modelos fallan."""
    from src.services.gemini_service import generate_content_with_fallback
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("all fail")

    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "key",
        "GEMINI_MODEL": "model-1",
        "GEMINI_MODEL_FALLBACK_1": "model-2",
        "GEMINI_MODEL_FALLBACK_2": "model-3",
    }):
        with pytest.raises(RuntimeError, match="All fallback models failed"):
            generate_content_with_fallback(mock_client, "prompt", config=None)


def test_is_spanish_and_is_english_stopwords():
    """Validar detección de idioma por stopwords."""
    from src.services.gemini_service import is_spanish, is_english

    # Español claro
    assert is_spanish("Buscamos desarrollador con experiencia en React y TypeScript.") is True
    # Inglés claro no es español
    assert is_spanish("We are looking for a developer with experience in React.") is False

    # Inglés claro
    assert is_english("We are looking for a developer with experience and required skills.") is True
    # Español no es inglés
    assert is_english("Buscamos desarrollador con experiencia en el desarrollo de sistemas.") is False
