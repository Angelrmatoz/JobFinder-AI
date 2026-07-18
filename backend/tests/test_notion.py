import pytest
from unittest.mock import MagicMock, patch
from src.services.notion_service import save_job_to_notion

def test_save_job_to_notion_skipped_missing_env(mock_job_detail):
    """Validar que la integración con Notion retorne False si faltan las variables de entorno."""
    with patch.dict("os.environ", {}, clear=True):
        result = save_job_to_notion(mock_job_detail)
        assert result is False

def test_save_job_to_notion_success(mock_job_detail):
    """Validar almacenamiento exitoso mockeando la llamada a notion_client."""
    mock_notion_instance = MagicMock()
    
    with patch("src.services.notion_service.Client") as MockClient:
        MockClient.return_value = mock_notion_instance
        
        with patch.dict("os.environ", {
            "NOTION_API_KEY": "secret_notion_token",
            "NOTION_DATABASE_ID": "database_uuid_123"
        }):
            result = save_job_to_notion(mock_job_detail)
            
            assert result is True
            MockClient.assert_called_once_with(auth="secret_notion_token")
            mock_notion_instance.pages.create.assert_called_once()
            
            # Verificar formato del payload que enviamos a Notion
            call_kwargs = mock_notion_instance.pages.create.call_args[1]
            assert call_kwargs["parent"] == {"database_id": "database_uuid_123"}
            
            props = call_kwargs["properties"]
            assert props["Título"]["title"][0]["text"]["content"] == mock_job_detail.title
            assert props["Empresa"]["rich_text"][0]["text"]["content"] == mock_job_detail.company
            assert props["Ubicación"]["rich_text"][0]["text"]["content"] == mock_job_detail.location
            assert props["Enlace"]["url"] == mock_job_detail.link
            assert props["Match Score"]["number"] == mock_job_detail.match_score
            assert props["Consejo para Aplicar"]["rich_text"][0]["text"]["content"] == mock_job_detail.apply_tip

def test_save_job_to_notion_api_error(mock_job_detail):
    """Validar control de errores si la llamada a la API de Notion falla."""
    mock_notion_instance = MagicMock()
    mock_notion_instance.pages.create.side_effect = Exception("Notion API Error")
    
    with patch("src.services.notion_service.Client") as MockClient:
        MockClient.return_value = mock_notion_instance
        
        with patch.dict("os.environ", {
            "NOTION_API_KEY": "secret_token",
            "NOTION_DATABASE_ID": "database_uuid"
        }):
            result = save_job_to_notion(mock_job_detail)
            assert result is False
            mock_notion_instance.pages.create.assert_called_once()
