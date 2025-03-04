import sys

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
        self.progress = {}
        self.solutions = {}
        self.permissions = []
        self.release = None
        self.load_constants()

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
                self.html[main_entry.id]["ee"] = main_entry.ee
            obfuscations = Obfuscation.query.with_entities(Obfuscation.id, Obfuscation.obfuscated_key).all()
            self.obfuscations = {i: o for i, o in obfuscations}
            self.obfuscations |= {o: i for i, o in obfuscations}
            html_nums = Obfuscation.query.with_entities(Obfuscation.id, Obfuscation.html_key).all()
            self.html_nums = {i: o for i, o in html_nums}
            self.html_nums |= {o: i for i, o in html_nums}
            solutions = Solution.query.with_entities(Solution.id, Solution.part1, Solution.part2).all()
            self.solutions = {i: {"part1": a, "part2": b} for i, a, b in solutions}
            permissions = Permissions.query.with_entities(Permissions.user_id).all()
            self.permissions = [permission[0] for permission in permissions]
            self.release = Release.query.first().release

    def load_progress(self, user_id: str) -> bool:
        """Load all variable data from the database into memory."""
        with self.app.app_context():
            progress = Progress.query.filter_by(user_id=user_id).first()
            if progress is None:
                return False
            self.progress = progress.__dict__.copy()
            self.progress.pop('_sa_instance_state', None)
        return True

    def update_progress(self, challenge_num: int, index: int) -> bool:
        """Update individual user progress in the database and refresh the cache."""
        user_id = self.progress["user_id"]
        with self.app.app_context():
            progress = Progress.query.filter_by(user_id=user_id).first()
            if progress is None:
                return False
            challenge = getattr(progress, f"c{challenge_num}", None)
            challenge[index] = True
            db.session.commit()
            self.load_progress()
        return True

    def add_user(self, user_id: str, name: str) -> bool:
        """Insert a new progress record into the database."""
        try:
            with self.app.app_context():
                new_progress = Progress(
                    user_id=user_id,
                    name=name,
                    **{f"c{i}": [False, False] for i in range(1, 11)}
                )
                db.session.add(new_progress)
                db.session.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            db.session.rollback()
            return False
