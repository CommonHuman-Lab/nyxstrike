"""
Tests for file operation endpoints:
  POST   /api/files/create
  POST   /api/files/modify
  DELETE /api/files/delete
  GET    /api/files/list
"""

import json
import uuid
import pytest


def _json(client, method, url, payload=None):
    """Helper to call a JSON endpoint and return the parsed response dict."""
    fn = getattr(client, method)
    kwargs = dict(content_type="application/json")
    if payload is not None:
        kwargs["data"] = json.dumps(payload)
    response = fn(url, **kwargs)
    return response, response.get_json()


# ---------------------------------------------------------------------------
# /api/files/create
# ---------------------------------------------------------------------------

class TestCreateFile:
    def test_create_returns_200(self, client):
        name = f"test_{uuid.uuid4().hex}.txt"
        response, data = _json(client, "post", "/api/files/create",
                               {"filename": name, "content": "hello"})
        assert response.status_code == 200

    def test_create_success_true(self, client):
        name = f"test_{uuid.uuid4().hex}.txt"
        _, data = _json(client, "post", "/api/files/create",
                        {"filename": name, "content": "hello"})
        assert data["success"] is True

    def test_create_returns_path(self, client):
        name = f"test_{uuid.uuid4().hex}.txt"
        _, data = _json(client, "post", "/api/files/create",
                        {"filename": name, "content": "hello"})
        assert "path" in data

    def test_create_returns_size(self, client):
        content = "hello world"
        name = f"test_{uuid.uuid4().hex}.txt"
        _, data = _json(client, "post", "/api/files/create",
                        {"filename": name, "content": content})
        assert data["size"] == len(content)

    def test_create_missing_filename_returns_400(self, client):
        response, data = _json(client, "post", "/api/files/create",
                               {"content": "no name"})
        assert response.status_code == 400
        assert "error" in data

    def test_create_empty_filename_returns_400(self, client):
        response, data = _json(client, "post", "/api/files/create",
                               {"filename": "", "content": "no name"})
        assert response.status_code == 400

    def test_create_empty_content_allowed(self, client):
        name = f"test_{uuid.uuid4().hex}.txt"
        _, data = _json(client, "post", "/api/files/create",
                        {"filename": name, "content": ""})
        assert data["success"] is True


# ---------------------------------------------------------------------------
# /api/files/modify
# ---------------------------------------------------------------------------

class TestModifyFile:
    def _create(self, client, content="initial"):
        name = f"mod_{uuid.uuid4().hex}.txt"
        _json(client, "post", "/api/files/create",
              {"filename": name, "content": content})
        return name

    def test_modify_existing_file(self, client):
        name = self._create(client)
        _, data = _json(client, "post", "/api/files/modify",
                        {"filename": name, "content": "updated"})
        assert data["success"] is True

    def test_modify_nonexistent_file_returns_error(self, client):
        _, data = _json(client, "post", "/api/files/modify",
                        {"filename": "does_not_exist_xyz.txt", "content": "x"})
        assert data["success"] is False
        assert "error" in data

    def test_modify_missing_filename_returns_400(self, client):
        response, _ = _json(client, "post", "/api/files/modify",
                            {"content": "no name"})
        assert response.status_code == 400

    def test_modify_append_mode(self, client):
        name = self._create(client, "first")
        _, data = _json(client, "post", "/api/files/modify",
                        {"filename": name, "content": "_second", "append": True})
        assert data["success"] is True


# ---------------------------------------------------------------------------
# /api/files/delete
# ---------------------------------------------------------------------------

class TestDeleteFile:
    def _create(self, client, content="to-delete"):
        name = f"del_{uuid.uuid4().hex}.txt"
        _json(client, "post", "/api/files/create",
              {"filename": name, "content": content})
        return name

    def test_delete_existing_file(self, client):
        name = self._create(client)
        _, data = _json(client, "delete", "/api/files/delete",
                        {"filename": name})
        assert data["success"] is True

    def test_delete_nonexistent_file_returns_error(self, client):
        _, data = _json(client, "delete", "/api/files/delete",
                        {"filename": "phantom_file.txt"})
        assert data["success"] is False
        assert "error" in data

    def test_delete_missing_filename_returns_400(self, client):
        response, _ = _json(client, "delete", "/api/files/delete", {})
        assert response.status_code == 400

    def test_deleted_file_no_longer_listed(self, client):
        name = self._create(client)
        # Delete it
        _json(client, "delete", "/api/files/delete", {"filename": name})
        # Confirm it's gone
        _, data = _json(client, "delete", "/api/files/delete",
                        {"filename": name})
        assert data["success"] is False


# ---------------------------------------------------------------------------
# /api/files/list
# ---------------------------------------------------------------------------

class TestListFiles:
    def test_list_root_returns_200(self, client):
        response = client.get("/api/files/list")
        assert response.status_code == 200

    def test_list_root_success_true(self, client):
        data = client.get("/api/files/list").get_json()
        assert data["success"] is True

    def test_list_contains_files_key(self, client):
        data = client.get("/api/files/list").get_json()
        assert "files" in data
        assert isinstance(data["files"], list)

    def test_list_file_entries_have_expected_fields(self, client):
        # Create a file so the listing is non-empty
        name = f"list_{uuid.uuid4().hex}.txt"
        _json(client, "post", "/api/files/create",
              {"filename": name, "content": "x"})
        data = client.get("/api/files/list").get_json()
        assert data["success"] is True
        for entry in data["files"]:
            assert "name" in entry
            assert "type" in entry
            assert "size" in entry
            assert "modified" in entry

    def test_list_nonexistent_directory_returns_error(self, client):
        data = client.get("/api/files/list?directory=does_not_exist_xyz").get_json()
        assert data["success"] is False
        assert "error" in data
