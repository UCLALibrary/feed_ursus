from pathlib import Path

import pytest
from packaging.version import Version

from feed_ursus.feed_ursus import PyPIResponse, importlib, is_outdated, requests


def test_pypi_response() -> None:
    result = PyPIResponse.model_validate_json(
        Path("tests/fixtures/pypi-response.json").read_text()
    )
    assert result.info.version == "2.0.3"


class TestIsOutdated:
    @pytest.mark.parametrize(
        ["local_version", "latest_version"],
        [
            ("1.1.1", "1.1.2"),
            ("2.2.2", "2.3.0"),
            ("3.3.3", "4.0.0"),
        ],
    )
    def test_outdated(
        self,
        local_version: str,
        latest_version: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class FakePyPIResponse:
            def json(self):
                return {"info": {"version": latest_version}}

        monkeypatch.setattr(
            requests,
            "get",
            lambda _url: FakePyPIResponse(),
        )
        monkeypatch.setattr(
            importlib.metadata,
            "version",
            lambda _package: local_version,
        )

        result = is_outdated()
        assert result == Version(
            latest_version
        )  # returns the current highest version from pypi
        assert result  # result must be truthy

    @pytest.mark.parametrize(
        ["local_version", "latest_version"],
        [
            ("1.1.1", "1.1.1"),
            ("2.2.2", "2.2.1"),
            ("1.1.1.dev0+g998083fc3.d20260403", "1.1.1"),
            # *any* dev version = not outdated
            ("1.1.1.dev0+g998083fc3.d20260403", "1.1.2"),
        ],
    )
    def test_not_outdated(
        self,
        local_version: str,
        latest_version: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class FakePyPIResponse:
            def json(self):
                return {"info": {"version": latest_version}}

        monkeypatch.setattr(
            requests,
            "get",
            lambda _url: FakePyPIResponse(),
        )
        monkeypatch.setattr(
            importlib.metadata,
            "version",
            lambda _package: local_version,
        )

        result = is_outdated()
        assert result == False
        assert not result  # result is not truthy (should be obvious here)
