"""
Tests para el validador de resolución de pantalla.

Pruebas unitarias para ScreenValidator.
"""

from unittest.mock import MagicMock, patch

from utils.screen_validator import ScreenValidator


class TestScreenValidator:
    """Tests para validación de resolución de pantalla."""

    def test_validate_resolution_sufficient(self):
        """Test resolución suficiente (>= mínimo)."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1920, 1080)
        ):
            assert ScreenValidator.validate_resolution() is True

    def test_validate_resolution_minimum(self):
        """Test resolución exactamente en el mínimo."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1280, 720)
        ):
            assert ScreenValidator.validate_resolution() is True

    def test_validate_resolution_insufficient_width(self):
        """Test resolución insuficiente por ancho."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1024, 768)
        ):
            assert ScreenValidator.validate_resolution() is False

    def test_validate_resolution_insufficient_height(self):
        """Test resolución insuficiente por altura."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1280, 600)
        ):
            assert ScreenValidator.validate_resolution() is False

    def test_validate_resolution_insufficient_both(self):
        """Test resolución insuficiente en ambas dimensiones."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(800, 600)
        ):
            assert ScreenValidator.validate_resolution() is False

    def test_get_resolution_info_sufficient(self):
        """Test información de resolución suficiente."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1920, 1080)
        ):
            info = ScreenValidator.get_resolution_info()
            assert "1920x1080" in info
            assert "✅ Adecuada" in info

    def test_get_resolution_info_insufficient(self):
        """Test información de resolución insuficiente."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1024, 768)
        ):
            info = ScreenValidator.get_resolution_info()
            assert "1024x768" in info
            assert "❌ Insuficiente" in info

    def test_resolution_constants(self):
        """Test que las constantes están definidas correctamente."""
        assert ScreenValidator.MIN_WIDTH == 1280
        assert ScreenValidator.MIN_HEIGHT == 720
        assert ScreenValidator.RECOMMENDED_WIDTH == 1920
        assert ScreenValidator.RECOMMENDED_HEIGHT == 1080

    def test_recommended_resolution_higher_than_minimum(self):
        """Test que la resolución recomendada es mayor que la mínima."""
        assert ScreenValidator.RECOMMENDED_WIDTH > ScreenValidator.MIN_WIDTH
        assert ScreenValidator.RECOMMENDED_HEIGHT > ScreenValidator.MIN_HEIGHT

    @patch('utils.ui_helpers.get_corporate_icon')
    @patch('utils.screen_validator.QMessageBox')
    def test_show_resolution_warning_insufficient(self, mock_msgbox, mock_icon):
        """Test mostrar advertencia con resolución insuficiente."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1024, 768)
        ):
            mock_msgbox_instance = MagicMock()
            mock_msgbox.return_value = mock_msgbox_instance
            mock_icon.return_value = MagicMock()

            result = ScreenValidator.show_resolution_warning()

            assert result is False
            # Verificar que se creó el message box
            assert mock_msgbox.called or mock_msgbox_instance.exec.called

    @patch('utils.ui_helpers.get_corporate_icon')
    @patch('utils.screen_validator.QMessageBox')
    def test_show_resolution_warning_below_recommended(self, mock_msgbox, mock_icon):
        """Test mostrar advertencia con resolución por debajo de lo recomendado."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1366, 768)
        ):
            mock_msgbox_instance = MagicMock()
            mock_msgbox.return_value = mock_msgbox_instance
            mock_msgbox_instance.exec.return_value = 16384  # Yes button
            mock_icon.return_value = MagicMock()

            ScreenValidator.show_resolution_warning()

            # Debería llamar al message box
            assert mock_msgbox.called or mock_msgbox_instance.exec.called

    @patch('utils.screen_validator.QMessageBox')
    def test_show_resolution_warning_optimal(self, mock_msgbox):
        """Test no mostrar advertencia con resolución óptima."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1920, 1080)
        ):
            ScreenValidator.show_resolution_warning()

            # No se debería haber llamado QMessageBox
            assert not mock_msgbox.called

    def test_validate_4k_resolution(self):
        """Test validación con resolución 4K."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(3840, 2160)
        ):
            assert ScreenValidator.validate_resolution() is True

    def test_validate_edge_case_one_pixel_below(self):
        """Test caso borde: un pixel por debajo del mínimo."""
        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1279, 720)
        ):
            assert ScreenValidator.validate_resolution() is False

        with patch.object(
            ScreenValidator,
            'get_screen_resolution',
            return_value=(1280, 719)
        ):
            assert ScreenValidator.validate_resolution() is False
