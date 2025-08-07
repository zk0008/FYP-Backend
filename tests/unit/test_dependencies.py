from unittest.mock import Mock, patch

from app.dependencies import get_settings, get_supabase


class TestDependencies:
    @patch("app.dependencies.Settings")
    def test_get_settings(self, mock_settings_class):
        """
        Given the Settings class
        When get_settings is called
        Then it should return an instance of Settings
        """
        mock_instance = Mock()
        mock_settings_class.return_value = mock_instance

        get_settings.cache_clear()
        result = get_settings()

        assert result == mock_instance
        mock_settings_class.assert_called_once()


    @patch("app.dependencies.create_client")
    @patch("app.dependencies.get_settings")
    def test_get_supabase(self, mock_get_settings, mock_create_client):
        """
        Given the create_client function and get_settings
        When get_supabase is called
        Then it should return a Supabase client instance
        """
        mock_settings = Mock()
        mock_settings.SUPABASE_URL = "http://test.supabase.co"
        mock_settings.SUPABASE_SERVICE_ROLE_KEY = "test_service_key"
        mock_get_settings.return_value = mock_settings

        mock_supabase_client = Mock()
        mock_create_client.return_value = mock_supabase_client

        get_supabase.cache_clear()
        result = get_supabase()

        assert result == mock_supabase_client
        mock_create_client.assert_called_once_with(
            "http://test.supabase.co",  # Supabase URL
            "test_service_key"  # Supabase service role key
        )
