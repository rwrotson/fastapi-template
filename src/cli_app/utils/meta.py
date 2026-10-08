import json
import re
from dataclasses import dataclass
from email.utils import parseaddr
from functools import cache
from importlib import metadata
from pathlib import Path
from typing import Self, TypedDict, cast


class DependencyDict(TypedDict):
    name: str
    version: str


class ContactDict(TypedDict):
    name: str
    email: str


class MetaDict(TypedDict, total=False):
    metadata_version: str
    name: str
    version: str
    summary: str
    description: str
    authors: list[ContactDict]
    maintainers: list[ContactDict]
    classifiers: list[str]
    keywords: list[str]
    requires_python: str
    readme: str
    license_file: str
    url: str
    dependencies: list[DependencyDict]


@dataclass(slots=True, frozen=True)
class Meta:
    """Class parsing metadata."""

    data: MetaDict

    @staticmethod
    def _find_dist_name_from_direct_url(pkg_file: Path) -> str | None:
        """Find the distribution name by scanning direct_url.json for editable installs."""
        for dist in metadata.distributions():
            raw = dist.read_text("direct_url.json")
            if raw:
                try:
                    url = json.loads(raw).get("url", "")
                    dist_dir = Path(url.removeprefix("file://"))
                    if pkg_file.is_relative_to(dist_dir):
                        return dist.name
                except (ValueError, TypeError):
                    continue
        return None

    @classmethod
    def load_from_installed_package(cls) -> Self:
        """Find and load distribution metadata for the installed package containing this file."""
        pkg_file = Path(__file__).resolve()

        # For editable installs uv_build uses a .pth file and omits top_level.txt,
        # so packages_distributions() won't find us. Instead, find the distribution
        # whose direct_url.json points to a directory that contains this file.
        dist_name = cls._find_dist_name_from_direct_url(pkg_file)

        # Fall back to packages_distributions() for non-editable installs.
        if dist_name is None:
            top_level_pkg = __package__.split(".")[0] if __package__ else None
            if top_level_pkg:
                dist_names = metadata.packages_distributions().get(top_level_pkg)
                if dist_names:
                    dist_name = dist_names[0]

        if dist_name is None:
            return cls(data=cls._get_fallback_meta("Unknown"))

        try:
            meta_json = metadata.metadata(dist_name).json

            author_email = cast(str, meta_json.pop("author_email", ""))
            requires_dist = meta_json.pop("requires_dist", [])

            meta_dict_keys = MetaDict.__annotations__.keys()
            meta = cast(MetaDict, {k: v for k, v in meta_json.items() if k in meta_dict_keys})

            authors: list[ContactDict] = []
            for author_string in author_email.split(","):
                name, email = parseaddr(author_string)
                authors.append({"name": name, "email": email})
            meta["authors"] = authors
            meta["dependencies"] = cls._get_installed_dependencies(cast(list[str], requires_dist))

            return cls(data=meta)

        except metadata.PackageNotFoundError:
            return cls(data=cls._get_fallback_meta(dist_name))

    @staticmethod
    def _get_installed_dependencies(requires_dist: list[str]) -> list[DependencyDict]:
        """Resolve declared dependencies to their installed versions."""
        pkg_name_pattern = re.compile(r"^[a-zA-Z0-9._-]+")
        pkg_names = [
            m.group(0).lower()
            for s in requires_dist
            if (m := pkg_name_pattern.match(s)) is not None
        ]

        installed: dict[str, str] = {}
        for dist in metadata.distributions():
            if dist.name.lower() in pkg_names:
                installed[dist.name] = dist.version

        return [{"name": name, "version": version} for name, version in sorted(installed.items())]

    @staticmethod
    def _get_fallback_meta(pkg_name: str) -> MetaDict:
        """Return a placeholder MetaDict when the real distribution cannot be found."""
        return {
            "name": f"{pkg_name} (not installed)",
            "version": "0.0.0-dev",
            "description": "Project metadata unavailable.",
            "dependencies": [],
        }

    def __getitem__(self, item: str) -> str | list[ContactDict] | list[DependencyDict] | None:
        return cast(str | list[ContactDict] | list[DependencyDict] | None, self.data.get(item))

    def __str__(self) -> str:
        return str(self.data)


@cache
def get_project_meta() -> Meta:
    """Fetch the project metadata using the Meta class."""
    return Meta.load_from_installed_package()
