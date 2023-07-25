# This new model allows for a many to many relationship
# Because items can have multiple tags and tags can have multiple items we need a secondary (linking) table

from db import db


class ItemsTags(db.Model):
    __tablename__ = "items_tags"

    id = db.Column(db.Integer, primary_key=True)
    # Link to items using a foreign key
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    # Link to tags using a foreign key
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"))