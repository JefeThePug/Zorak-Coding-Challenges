from flask import Flask

from models import (
    db,
    DiscordID,
    MainEntry,
    SubEntry,
    Obfuscation,
    Progress,
    Solution,
    Permissions,
    Release,
)


class DataCache:
    def __init__(self, app: Flask):
        self.app = app
        self.discord_ids = {}
        self.html = {}
        self.obfuscations = {}
        self.html_nums = {}
        self.progresses = []
        self.solutions = {}
        self.permissions = []
        self.release = None
        self.load_constants()
        self.load_progress()

    def load_constants(self) -> None:
        """Load all pseudo-constant data from the database into memory."""
        with self.app.app_context():
            discord_ids = DiscordID.query.with_entities(DiscordID.name, DiscordID.discord_id).all()
            self.discord_ids = {name: i for name, i in discord_ids}
            main_entries = MainEntry.query.all()  # Get all main entries
            for main_entry in main_entries:
                self.html[main_entry.id] = {}
                sub_entries = SubEntry.query.filter_by(main_entry_id=main_entry.id).all()
                for sub_entry in sub_entries:
                    self.html[main_entry.id][sub_entry.sub_entry_id] = {
                        "title": sub_entry.title,
                        "content": sub_entry.content,
                        "instructions": sub_entry.instructions,
                        "input": sub_entry.input_type,
                        "form": sub_entry.form,
                        "solution": sub_entry.solution
                    }
            obfuscations = Obfuscation.query.with_entities(Obfuscation.id, Obfuscation.obfuscated_key).all()
            self.obfuscations = {i: o for i, o in obfuscations}
            self.obfuscations += {o: i for i, o in obfuscations}
            html_nums = Obfuscation.query.with_entities(Obfuscation.id, Obfuscation.html_key).all()
            self.html_nums = {i: o for i, o in html_nums}
            solutions = Solution.query.with_entities(Solution.id, Solution.part1, Solution.part2).all()
            self.solutions = {i: {"part1": a, "part2": b} for i, a, b in solutions}
            permissions = Permissions.query.with_entities(Permissions.user_id).all()
            self.permissions = [permission[0] for permission in permissions]
            self.release = Release.query.first().release

    def load_progress(self) -> None:
        """Load all variable data from the database into memory."""
        with self.app.app_context():
            self.progresses = Progress.query.all()

    def get_discord_ids(self) -> list[DiscordID]:
        """Return the cached DiscordIDs."""
        return self.discord_ids

    def update_discord_id(self, id: int, name: str, discord_id: str) -> None:
        """Update a DiscordID in the database and refresh the cache."""
        with self.app.app_context():  # Use the app context
            discord_id_entry = DiscordID.query.get(id)
            if discord_id_entry:
                discord_id_entry.name = name
                discord_id_entry.discord_id = discord_id
                db.session.commit()
                self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh all cached data from the database."""
        self.load_data()
