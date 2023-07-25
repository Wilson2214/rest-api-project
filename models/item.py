from db import db

# Mapping from Python to SQL Database by creating a database model class
class ItemModel(db.Model):
    # Define the name of the table
    __tablename__ = "items"

    # Define the attributes in the table and their unique characteristics (data type, whether or not nullable, primary keys)

    # In this case the primary key is id
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False)
    description = db.Column(db.String)
    price = db.Column(db.Float(precision=2), unique = False, nullable = False)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), unique = False, nullable = False)

    # We also create a relationship with our Store Model (need two ends to the relationship)
    # item has a store_id which links one item with one store
    # on the other end stores has a relationship with this table to pull all items that match the store's id
    # Store variable will be populated by a storemodel object whose id matches the foreign key
    # back_populates means we can easily see all items within the store
    store = db.relationship("StoreModel", back_populates="items")

    # We also need to create a relationship to the tags model
    tags = db.relationship("TagModel", back_populates="items", secondary="items_tags")