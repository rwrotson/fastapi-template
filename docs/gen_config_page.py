"""Generate docs/configuration.md from .env.example at docs build time."""  # noqa: INP001

from pathlib import Path

import mkdocs_gen_files

env_example = Path(__file__).parent.parent / ".env.example"
lines = env_example.read_text().splitlines()

sections: list[tuple[str, list[tuple[str, str, str]]]] = []  # [(heading, [(var, default, desc)])]
current_heading = ""
current_rows: list[tuple[str, str, str]] = []

for line in lines:
    stripped = line.strip()
    if not stripped:
        continue
    if stripped.startswith("#") and "=" not in stripped:
        if current_heading:
            sections.append((current_heading, current_rows))
        current_heading = stripped.lstrip("# ").strip()
        current_rows = []
    elif "=" in stripped:
        # Split off inline comment
        if " #" in stripped:
            var_part, desc = stripped.split(" #", 1)
            desc = desc.strip()
        else:
            var_part, desc = stripped, ""
        var, _, default = var_part.partition("=")
        current_rows.append((var.strip(), default.strip(), desc))

if current_heading:
    sections.append((current_heading, current_rows))

md_lines: list[str] = [
    "# Configuration\n",
    "All settings are read from environment variables or a `.env` file in the project root.\n",
    "Copy `.env.example` to `.env` and uncomment the variables you want to override.\n",
]

for heading, rows in sections:
    md_lines.append(f"\n## {heading}\n")
    md_lines.append("| Variable | Default | Description |")
    md_lines.append("|----------|---------|-------------|")
    for var, default, desc in rows:
        default_cell = f"`{default}`" if default else "—"
        md_lines.append(f"| `{var}` | {default_cell} | {desc} |")

with mkdocs_gen_files.open("configuration.md", "w") as fd:
    fd.write("\n".join(md_lines) + "\n")

mkdocs_gen_files.set_edit_path("configuration.md", env_example)
