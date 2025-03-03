from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class DiscordID(db.Model):
    __tablename__ = 'discord_ids'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)
    discord_id = db.Column(db.String(20), nullable=False, unique=True)

class MainEntry(db.Model):
    __tablename__ = 'main_entries'

    id = db.Column(db.Integer, primary_key=True)
    ee = db.Column(db.Text)

class SubEntry(db.Model):
    __tablename__ = 'sub_entries'

    id = db.Column(db.Integer, primary_key=True)
    main_entry_id = db.Column(db.Integer, db.ForeignKey('main_entries.id', ondelete='CASCADE'))
    sub_entry_id = db.Column(db.Integer)
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    instructions = db.Column(db.Text)
    input_type = db.Column(db.Text)
    form = db.Column(db.Text)
    solution = db.Column(db.Text)
    main_entry = db.relationship('MainEntry', backref='sub_entries')

class Obfuscation(db.Model):
    __tablename__ = 'obfuscation'

    id = db.Column(db.Integer, primary_key=True)
    obfuscated_key = db.Column(db.String(255))
    html_key = db.Column(db.String(255))

class Progress(db.Model):
    __tablename__ = 'progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, unique=True)
    c1 = db.Column(db.ARRAY(db.Boolean))
    c2 = db.Column(db.ARRAY(db.Boolean))
    c3 = db.Column(db.ARRAY(db.Boolean))
    c4 = db.Column(db.ARRAY(db.Boolean))
    c5 = db.Column(db.ARRAY(db.Boolean))
    c6 = db.Column(db.ARRAY(db.Boolean))
    c7 = db.Column(db.ARRAY(db.Boolean))
    c8 = db.Column(db.ARRAY(db.Boolean))
    c9 = db.Column(db.ARRAY(db.Boolean))
    c10 = db.Column(db.ARRAY(db.Boolean))
    name = db.Column(db.String(255))

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    part1 = db.Column(db.Text)
    part2 = db.Column(db.Text)
