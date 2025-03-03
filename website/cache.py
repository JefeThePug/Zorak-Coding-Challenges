from models import db, DiscordID, MainEntry, Obfuscation, Progress, Solution, SubEntry

class DataCache:
    def __init__(self, app):
        self.discord_ids = []
        self.main_entries = []
        self.obfuscations = []
        self.progresses = []
        self.solutions = []
        self.sub_entries = []
        self.app = app
        self.load_data()

    def load_data(self):
        """Load all data from the database into memory."""
        with self.app.app_context():  # Use the app context
            self.discord_ids = DiscordID.query.all()
            self.main_entries = MainEntry.query.all()
            self.obfuscations = Obfuscation.query.all()
            self.progresses = Progress.query.all()
            self.solutions = Solution.query.all()
            self.sub_entries = SubEntry.query.all()

    def get_discord_ids(self):
        """Return the cached DiscordIDs."""
        return self.discord_ids

    def update_discord_id(self, id, name, discord_id):
        """Update a DiscordID in the database and refresh the cache."""
        with self.app.app_context():  # Use the app context
            discord_id_entry = DiscordID.query.get(id)
            if discord_id_entry:
                discord_id_entry.name = name
                discord_id_entry.discord_id = discord_id
                db.session.commit()
                self.refresh_data()

    def refresh_data(self):
        """Refresh all cached data from the database."""
        self.load_data()
