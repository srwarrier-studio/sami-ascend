import re
from pathlib import Path

DIRECTORY = Path(__file__).with_name("views")


VIEW_NAME = re.compile(r"CREATE VIEW IF NOT EXISTS (\w+)")


def view_script() -> str:
    statements = []
    for path in sorted(DIRECTORY.glob("*.sql")):
        text = path.read_text()
        if text.startswith("CREATE VIEW"):
            statements.append(f"DROP VIEW IF EXISTS {VIEW_NAME.match(text).group(1)};\n{text}")
    return "\n".join(statements)


def query(entity: str) -> str:
    return (DIRECTORY / f"{entity}.sql").read_text().strip()
