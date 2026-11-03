from pathlib import Path

DIRECTORY = Path(__file__).with_name("views")


def view_script() -> str:
    return "\n".join(path.read_text() for path in sorted(DIRECTORY.glob("*.sql")) if path.read_text().startswith("CREATE VIEW"))


def query(entity: str) -> str:
    return (DIRECTORY / f"{entity}.sql").read_text().strip()
