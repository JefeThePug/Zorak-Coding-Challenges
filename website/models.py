from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class DiscordID(db.Model):
    __tablename__ = 'discord_ids'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(10), nullable=False)
    discord_id: str = db.Column(db.String(20), nullable=False, unique=True)

class MainEntry(db.Model):
    __tablename__ = 'main_entries'

    id: int = db.Column(db.Integer, primary_key=True)
    ee: str = db.Column(db.Text)

class SubEntry(db.Model):
    __tablename__ = 'sub_entries'

    id: int = db.Column(db.Integer, primary_key=True)
    main_entry_id: int = db.Column(db.Integer, db.ForeignKey('main_entries.id', ondelete='CASCADE'))
    sub_entry_id: int = db.Column(db.Integer)
    title: str = db.Column(db.Text)
    content: str = db.Column(db.Text)
    instructions: str = db.Column(db.Text)
    input_type: str = db.Column(db.Text)
    form: str = db.Column(db.Text)
    solution: str = db.Column(db.Text)
    main_entry: MainEntry = db.relationship('MainEntry', backref='sub_entries')

class Obfuscation(db.Model):
    __tablename__ = 'obfuscation'

    id: int = db.Column(db.Integer, primary_key=True)
    obfuscated_key: str = db.Column(db.String(255))
    html_key: str = db.Column(db.String(255))

class Progress(db.Model):
    __tablename__ = 'progress'

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: str = db.Column(db.String(20), nullable=False, unique=True)
    c1: list[bool] = db.Column(db.ARRAY(db.Boolean))
    c2: list[bool] = db.Column(db.ARRAY(db.Boolean))
    c3: list[bool] = db.Column(db.ARRAY(db.Boolean))
    c4: list[bool] = db.Column(db.ARRAY(db.Boolean))
    c5: list[bool] = db.Column(db.ARRAY(db.Boolean))
    c6: list[bool] = db.Column(db.ARRAY(db.Boolean))
    c7: list[bool] = db.Column(db.ARRAY(db.Boolean))
    c8: list[bool] = db.Column(db.ARRAY(db.Boolean))
    c9: list[bool] = db.Column(db.ARRAY(db.Boolean))
    c10: list[bool] = db.Column(db.ARRAY(db.Boolean))
    name: str = db.Column(db.String(255))

class Solution(db.Model):
    __tablename__ = 'solutions'

    id: int = db.Column(db.Integer, primary_key=True)
    part1: str = db.Column(db.Text)
    part2: str = db.Column(db.Text)
