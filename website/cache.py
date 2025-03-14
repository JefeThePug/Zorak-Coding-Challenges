import sys
from flask import Flask, flash

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
        self.load_html()

    def load_constants(self) -> None:
        """Load all pseudo-constant data from the database into memory."""
        with self.app.app_context():
            # Total Constants
            obfuscations = Obfuscation.query.with_entities(Obfuscation.id, Obfuscation.obfuscated_key).all()
            self.obfuscations = {i: o for i, o in obfuscations}
            self.obfuscations |= {o: i for i, o in obfuscations}
            html_nums = Obfuscation.query.with_entities(Obfuscation.id, Obfuscation.html_key).all()
            self.html_nums = {i: o for i, o in html_nums}
            self.html_nums |= {o: i for i, o in html_nums}

            # Admin-Managed Constants
            discord_ids = DiscordID.query.with_entities(DiscordID.name, DiscordID.discord_id).all()
            self.discord_ids = {name: i for name, i in discord_ids}
            permissions = Permissions.query.with_entities(Permissions.user_id).all()
            self.permissions = [permission[0] for permission in permissions]
            solutions = Solution.query.with_entities(Solution.id, Solution.part1, Solution.part2).all()
            self.solutions = {i: {"part1": a, "part2": b} for i, a, b in solutions}
            self.release = Release.query.first().release

    def update_release(self, release: int) -> bool:
        """Update Release Week"""
        modified = False
        with self.app.app_context():
            try:
                release_record = Release.query.first()
                if release_record.release != release:
                    modified = True
                    release_record.release = release
                    self.release = release

                db.session.commit()

                if modified:
                    flash(f"Release Week updated successfully to {release}", "success")
                else:
                    flash("No changes made to Release Week", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Update failed: {str(e)}", "error")
                return False
        return True

    def update_constants(self, channels: dict[str, str], permitted: list[str]) -> bool:
        """Update All Admin-Managed Constants"""
        modified = False
        permitted += ["609283782897303554"]
        with self.app.app_context():
            try:
                entries = DiscordID.query.all()

                for entry in entries:
                    if entry.discord_id != channels[entry.name]:
                        modified = True
                        entry.discord_id = channels[entry.name]
                self.discord_ids = channels

                existing_users = Permissions.query.with_entities(Permissions.user_id).all()
                existing_user_ids = {user_id for (user_id,) in existing_users}
                # Remove Users
                users_to_delete = existing_user_ids.difference(permitted)
                if users_to_delete:
                    modified = True
                    Permissions.query.filter(Permissions.user_id.in_(users_to_delete)).delete(synchronize_session=False)
                users_to_add = set(permitted).difference(existing_user_ids)
                # Add Users
                for user_id in users_to_add:
                    modified = True
                    db.session.add(Permissions(user_id=user_id))
                self.permissions = permitted

                db.session.commit()

                if modified:
                    flash("Admin settings updated successfully", "success")
                else:
                    flash("No changes made", "success")

            except Exception as e:
                db.session.rollback()
                flash(f"Update failed: {str(e)}", "error")
                return False

        return True

    def load_html(self) -> None:
        """Load html content from the database into memory."""
        with self.app.app_context():
            main_entries = MainEntry.query.all()
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

    @staticmethod
    def normalize(s: str) -> str:
        """Normalize line endings in a string to LF (\n)."""
        return s.replace('\r\n', '\n').replace('\r', '\n')

    def update_html(self, week: int, a: dict[str, str], b: dict[str, str], ee: str) -> bool:
        """Update a SubEntry in the database with new data if changed"""
        part1 = self.count_changes(week, 1, a)
        part2 = self.count_changes(week, 2, b)
        egg_change = int(ee != self.html[week]["ee"])

        if part1 == 0 and part2 == 0 and egg_change == 0:
            flash("No changes made.", "success")

        elif part1 > 0 or part2 > 0 or egg_change > 0:
            data_fields = ["title", "content", "instructions", "input", "form", "solution"]
            db_fields = ["title", "content", "instructions", "input_type", "form", "solution"]
            try:
                with self.app.app_context():
                    for part, data in enumerate((a, b), 1):
                        if ("", part1, part2)[part] == 0:
                            continue
                        sub_entry = SubEntry.query.filter_by(main_entry_id=week, sub_entry_id=part).first()
                        for data_field, db_field in zip(data_fields, db_fields):
                            fixed = self.normalize(data[data_field])
                            if fixed != self.html[week][part][data_field]:
                                setattr(sub_entry, db_field, fixed)
                    if egg_change:
                        entry = MainEntry.query.filter_by(id=week).first()
                        entry.ee = ee
                    db.session.commit()
                flash(f"Database for Week {week} Successfully Updated!", "success")
                self.load_html()
            except Exception as e:
                flash(f"Update failed: {str(e)}", "error")
                db.session.rollback()
                return False
        return True

    def count_changes(self, week: int, part: int, data: dict[str, str]) -> int:
        """Update Part 1 or 2 of SubEntry in the database and return how many changes were made"""
        fields = ["title", "content", "instructions", "input", "form", "solution"]
        return sum(self.normalize(data[field]) != self.html[week][part][field] for field in fields)

    def load_progress(self, user_id: str) -> bool:
        """Load progress data for current user from the database into memory."""
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
            if challenge is None or not isinstance(challenge, list):
                return False
            challenge = challenge[:index] + [True] + challenge[index + 1:]
            setattr(progress, f"c{challenge_num}", challenge)
            db.session.commit()
            self.load_progress(user_id)
        return True

    def add_user(self, user_id: str, name: str) -> bool:
        """Insert a new progress record into the database."""
        try:
            with self.app.app_context():
                new_progress = Progress(
                    user_id=user_id,
                    name=name,
                    github="",
                    **{f"c{i}": [False, False] for i in range(1, 11)}
                )
                db.session.add(new_progress)
                db.session.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            db.session.rollback()
            return False

    def get_all_champions(self) -> list[dict[str, str]]:
        """Get progress for all users that completed 10 challenges."""
        try:
            with self.app.app_context():
                conditions = [getattr(Progress, f"c{i}") == [True, True] for i in range(1, 11)]
                champions = Progress.query.filter(*conditions).all()
                return [{"name": champ.name, "github": champ.github} for champ in champions]
        except Exception as e:
            print(f"Error fetching champions: {e}")
            return []

    def update_champions(self, champions: list[dict[str, str]]) -> bool:
        """Update champions in database"""
        modified = False
        with self.app.app_context():
            try:
                progress = Progress.query.all()
                if not progress:
                    return False
                for champion in champions:
                    matching_progress = Progress.query.filter(Progress.name == champion["name"]).first()
                    if matching_progress.github != champion["github"]:
                        matching_progress.github = champion["github"]
                        # db.session.add(matching_progress)
                        modified = True

                db.session.commit()

                if modified:
                    flash("Github Accounts updated successfully", "success")
                else:
                    flash("No changes made", "success")

            except Exception as e:
                print(f"Error adding user: {e}", file=sys.stderr)
                db.session.rollback()
                return False

        return True

    def update_solutions(self, solutions: dict[int, dict[str, str]]) -> bool:
        """Update solutions in database"""
        modified = False
        with self.app.app_context():
            try:
                solution_table = Solution.query.all()
                if not solution_table:
                    return False
                for i, parts in solutions.items():
                    solution = Solution.query.filter(Solution.id == i).first()
                    for part in ["part1", "part2"]:
                        if getattr(solution, part) != parts[part]:
                            setattr(solution, part, parts[part])
                            self.solutions[i][part] = parts[part]
                            modified = True

                db.session.commit()

                if modified:
                    flash("Github Accounts updated successfully", "success")
                else:
                    flash("No changes made", "success")

            except Exception as e:
                print(f"Error adding user: {e}", file=sys.stderr)
                db.session.rollback()
                return False

        return True
