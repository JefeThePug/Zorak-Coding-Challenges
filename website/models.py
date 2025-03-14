from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


class DiscordID(db.Model):
    __tablename__ = 'discord_ids'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(10), nullable=False)
    discord_id: Mapped[str] = mapped_column(db.String(20), nullable=False)


class MainEntry(db.Model):
    __tablename__ = 'main_entries'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    ee: Mapped[str] = mapped_column(db.Text)


class SubEntry(db.Model):
    __tablename__ = 'sub_entries'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    main_entry_id: Mapped[int] = mapped_column(ForeignKey('main_entries.id', ondelete='CASCADE'))
    sub_entry_id: Mapped[int] = mapped_column(db.Integer)
    title: Mapped[str] = mapped_column(db.Text)
    content: Mapped[str] = mapped_column(db.Text)
    instructions: Mapped[str] = mapped_column(db.Text)
    input_type: Mapped[str] = mapped_column(db.Text)
    form: Mapped[str] = mapped_column(db.Text)
    solution: Mapped[str] = mapped_column(db.Text)

    # Define the relationship
    main_entry: Mapped[MainEntry] = db.relationship('MainEntry', backref='sub_entries')


class Obfuscation(db.Model):
    __tablename__ = 'obfuscation'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    obfuscated_key: Mapped[str] = mapped_column(db.String(255))
    html_key: Mapped[str] = mapped_column(db.String(255))


class Progress(db.Model):
    __tablename__ = 'progress'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(db.String(20), nullable=False, unique=True)
    c1: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c2: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c3: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c4: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c5: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c6: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c7: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c8: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c9: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    c10: Mapped[list[bool]] = mapped_column(db.ARRAY(db.Boolean))
    name: Mapped[str] = mapped_column(db.String(255))
    github: Mapped[str] = mapped_column(db.String(255))


class Solution(db.Model):
    __tablename__ = 'solutions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    part1: Mapped[str] = mapped_column(db.Text)
    part2: Mapped[str] = mapped_column(db.Text)


class Permissions(db.Model):
    __tablename__ = 'permissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(db.String(20))


class Release(db.Model):
    __tablename__ = 'release'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    release: Mapped[int] = mapped_column(db.Integer)
