from datetime import date

from butterfly.infrastructure.memory.story_seed import StorySeed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.seeder import derive_documents


class Derivation:
    def __init__(self, db: Database, story: StorySeed, today: date):
        self.db = db
        self.story = story
        self.today = today

    def refresh(self) -> None:
        with self.db.transaction():
            derive_documents(self.db, self.story, self.today)
