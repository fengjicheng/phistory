from phistory.models import AgentSpec, VersionInfo
from phistory.npm import all_versions, versions_between


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
        "phistory.npm.all_versions",
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
        "phistory.npm.npm_view",
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
