import re

from cli_app.utils.meta import Meta, MetaDict, get_project_meta


def test_fallback_meta() -> None:
    meta = Meta._get_fallback_meta("MyPkg")  # noqa: SLF001
    assert meta["name"] == "MyPkg (not installed)"
    assert meta["version"] == "0.0.0-dev"
    assert meta["dependencies"] == []


def test_load_from_installed_package_name_and_version() -> None:
    m = Meta.load_from_installed_package()
    assert m["name"] == "cli-app"
    assert re.match(r"\d+\.\d+\.\d+", str(m["version"]))


def test_meta_getitem_present_key() -> None:
    data: MetaDict = {"name": "test-app", "version": "1.2.3"}
    m = Meta(data=data)
    assert m["name"] == "test-app"
    assert m["version"] == "1.2.3"


def test_meta_getitem_missing_key_returns_none() -> None:
    data: MetaDict = {"name": "test-app"}
    m = Meta(data=data)
    assert m["nonexistent_key"] is None


def test_meta_str_contains_data() -> None:
    data: MetaDict = {"name": "test-app"}
    m = Meta(data=data)
    assert "test-app" in str(m)


def test_get_installed_dependencies_empty_input() -> None:
    deps = Meta._get_installed_dependencies([])  # noqa: SLF001
    assert deps == []


def test_get_installed_dependencies_known_package() -> None:
    # typer is a declared dependency of this project and must be installed.
    deps = Meta._get_installed_dependencies(["typer>=0.16.0"])  # noqa: SLF001
    assert "typer" in {d["name"].lower() for d in deps}


def test_get_installed_dependencies_returns_sorted() -> None:
    deps = Meta._get_installed_dependencies(["typer>=0.16.0", "pydantic-settings>=2.0"])  # noqa: SLF001
    names = [d["name"] for d in deps]
    assert names == sorted(names)


def test_get_project_meta_is_cached() -> None:
    assert get_project_meta() is get_project_meta()
