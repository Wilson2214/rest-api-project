from db import db

# Mapping from Python to SQL Database by creating a database model class
class StoreModel(db.Model):
    # Define the name of the table
    __tablename__ = "stores"

    # Define the attributes in the table and their unique characteristics (data type, whether or not nullable, primary keys)

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), unique = True, nullable = False)

    # We also create a relationship with our Item Model (need two ends to the relationship)

    # lazy means the items won't be fetched from the database until we tell it to (will speed up the query)
    # cascade is used to prevent errors. If a store is deleted, we delete all items in that store as the store is the parent
    items = db.relationship("ItemModel", back_populates="store", lazy="dynamic", cascade="all, delete")

    # We also create a relationship to tags
    tags = db.relationship("TagModel", back_populates="store", lazy="dynamic")