import pytest
from unittest.mock import MagicMock, patch
from src.services.pdf_service import extract_text_from_pdf

def test_extract_text_from_pdf_success():
    """Validar extracción exitosa de texto simulando las páginas de PdfReader."""
    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = "Nombre: Juan Pérez\nHabilidades: Python, React"
    
    mock_page_2 = MagicMock()
    mock_page_2.extract_text.return_value = "Experiencia: 3 años de desarrollador."
    
    with patch("src.services.pdf_service.PdfReader") as MockPdfReader:
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page_1, mock_page_2]
        MockPdfReader.return_value = mock_reader
        
        result = extract_text_from_pdf(b"fake_pdf_bytes")
        
        assert "Juan Pérez" in result
        assert "Habilidades: Python, React" in result
        assert "Experiencia: 3 años de desarrollador." in result
        MockPdfReader.assert_called_once()

def test_extract_text_from_pdf_failure():
    """Validar lanzamiento de error si falla la lectura del archivo PDF."""
    with patch("src.services.pdf_service.PdfReader", side_effect=Exception("Corrupted PDF")):
        with pytest.raises(ValueError) as excinfo:
            extract_text_from_pdf(b"corrupted_pdf_bytes")
        assert "Failed to parse PDF file: Corrupted PDF" in str(excinfo.value)
