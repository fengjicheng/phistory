from phistory.models import AgentSpec, VersionInfo
from phistory.packages import all_versions, latest_version, versions_between


def test_versions_between_uses_registry_order(monkeypatch):
    agent = AgentSpec(
        id="x",
        display_name="X",
        package="x",
        tap_client="x",
        fake_env={},
        run_args=(),
    )
    monkeypatch.setattr(
        "phistory.packages.all_versions",
        lambda _agent, **_kwargs: [VersionInfo("1.0.0"), VersionInfo("1.1.0"), VersionInfo("2.0.0")],
    )

    assert [item.version for item in versions_between(agent, "1.1.0", "latest")] == ["1.1.0", "2.0.0"]


def test_all_versions_filters_platform_and_prerelease_versions(monkeypatch):
    agent = AgentSpec(
        id="x",
        display_name="X",
        package="x",
        tap_client="x",
        fake_env={},
        run_args=(),
    )
    monkeypatch.setattr(
        "phistory.packages.npm_view",
        lambda *_args: {
            "versions": ["1.0.0", "1.1.0-alpha.1", "1.1.0-linux-x64", "1.1.0"],
            "time": {},
        },
    )

    assert [item.version for item in all_versions(agent)] == ["1.0.0", "1.1.0"]
    assert [item.version for item in all_versions(agent, include_prerelease=True)] == [
        "1.0.0",
        "1.1.0-alpha.1",
        "1.1.0",
    ]


def test_pypi_versions_are_sorted_by_upload_time(monkeypatch):
    agent = AgentSpec(
        id="x",
        display_name="X",
        package="x",
        source="pypi",
        tap_client="x",
        fake_env={},
        run_args=(),
    )
    monkeypatch.setattr(
        "phistory.packages._pypi_json",
        lambda _package: {
            "info": {"version": "0.2.0"},
            "releases": {
                "0.2.0": [
                    {
                        "packagetype": "bdist_wheel",
                        "upload_time_iso_8601": "2026-05-02T00:00:00Z",
                        "url": "https://example.invalid/0.2.whl",
                    }
                ],
                "0.1.0": [
                    {
                        "packagetype": "bdist_wheel",
                        "upload_time_iso_8601": "2026-05-01T00:00:00Z",
                        "url": "https://example.invalid/0.1.whl",
                    }
                ],
                "0.3.0rc1": [
                    {
                        "packagetype": "bdist_wheel",
                        "upload_time_iso_8601": "2026-05-03T00:00:00Z",
                        "url": "https://example.invalid/0.3.whl",
                    }
                ],
            },
        },
    )

    assert latest_version(agent).version == "0.2.0"
    assert [item.version for item in all_versions(agent)] == ["0.1.0", "0.2.0"]
    assert [item.version for item in all_versions(agent, include_prerelease=True)] == ["0.1.0", "0.2.0", "0.3.0rc1"]


def test_github_release_versions_are_sorted_by_publish_time(monkeypatch):
    agent = AgentSpec(
        id="x",
        display_name="X",
        package="owner/repo",
        source="github-release",
        tap_client="x",
        fake_env={},
        run_args=(),
    )
    monkeypatch.setattr(
        "phistory.packages._github_releases",
        lambda _repo: [
            {
                "tag_name": "v2",
                "published_at": "2026-05-02T00:00:00Z",
                "html_url": "https://example.invalid/v2",
                "draft": False,
                "prerelease": False,
            },
            {
                "tag_name": "v1",
                "published_at": "2026-05-01T00:00:00Z",
                "html_url": "https://example.invalid/v1",
                "draft": False,
                "prerelease": False,
            },
            {
                "tag_name": "v3-beta",
                "published_at": "2026-05-03T00:00:00Z",
                "html_url": "https://example.invalid/v3-beta",
                "draft": False,
                "prerelease": True,
            },
        ],
    )

    assert latest_version(agent).version == "v2"
    assert [item.version for item in all_versions(agent)] == ["v1", "v2"]
    assert [item.version for item in all_versions(agent, include_prerelease=True)] == ["v1", "v2", "v3-beta"]
