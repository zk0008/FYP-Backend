import pytest
from pydantic import ValidationError

from app.constants import MIN_USERNAME_LENGTH, MAX_USERNAME_LENGTH
from app.models import GroupGPTRequest


class TestGroupGPTRequest:
    def test_valid_request(self):
        """
        Given valid request data
        When GroupGPTRequest is instantiated
        Then it should create an instance without raising an error
        """
        request = GroupGPTRequest(
            username="test_username",
            chatroom_id="test_chatroom_id",
            content="Test content."
        )

        assert request.username == "test_username"
        assert request.chatroom_id == "test_chatroom_id"
        assert request.content == "Test content."


    def test_missing_fields(self):
        """
        Given a request with missing fields
        When GroupGPTRequest is instantiated
        Then it should raise a ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            GroupGPTRequest()

        assert "Field required" in str(exc_info.value)


    def test_empty_username(self):
        """
        Given an empty username
        When GroupGPTRequest is instantiated
        Then it should raise a ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            GroupGPTRequest(
                username="",
                chatroom_id="test_chatroom_id",
                content="Test content."
            )

        assert f"String should have at least {MIN_USERNAME_LENGTH} characters" in str(exc_info.value)


    def test_username_too_long(self):
        """
        Given a username that exceeds the maximum length
        When GroupGPTRequest is instantiated
        Then it should raise a ValidationError
        """
        long_username = "a" * (MAX_USERNAME_LENGTH + 1)
        with pytest.raises(ValidationError) as exc_info:
            GroupGPTRequest(
                username=long_username,
                chatroom_id="test_chatroom_id",
                content="Test content."
            )

        assert f"String should have at most {MAX_USERNAME_LENGTH} characters" in str(exc_info.value)


    def test_invalid_username_type(self):
        """
        Given a non-string username
        When GroupGPTRequest is instantiated
        Then it should raise a ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            GroupGPTRequest(
                username=12345,
                chatroom_id="test_chatroom_id",
                content="Test content."
            )

        assert "Input should be a valid string" in str(exc_info.value)


    def test_invalid_chatroom_id_type(self):
        """
        Given a non-string chatroom_id
        When GroupGPTRequest is instantiated
        Then it should raise a ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            GroupGPTRequest(
                username="test_username",
                chatroom_id=12345,
                content="Test content."
            )

        assert "Input should be a valid string" in str(exc_info.value)


    def test_invalid_content_type(self):
        """
        Given a non-string content
        When GroupGPTRequest is instantiated
        Then it should raise a ValidationError
        """
        with pytest.raises(ValidationError) as exc_info:
            GroupGPTRequest(
                username="test_username",
                chatroom_id="test_chatroom_id",
                content=12345
            )

        assert "Input should be a valid string" in str(exc_info.value)


    def test_dict_conversion(self):
        """
        Given a valid GroupGPTRequest instance
        When converted to a dictionary
        Then it should match the original data
        """
        request = GroupGPTRequest(
            username="test_username",
            chatroom_id="test_chatroom_id",
            content="Test content."
        )

        request_dict = request.model_dump()
        assert isinstance(request_dict, dict)
        assert request_dict["username"] == "test_username"
        assert request_dict["chatroom_id"] == "test_chatroom_id"
        assert request_dict["content"] == "Test content."
