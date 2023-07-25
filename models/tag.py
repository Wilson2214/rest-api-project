from db import db

# Mapping from Python to SQL Database by creating a database model class
class TagModel(db.Model):
    # Define the name of the table
    __tablename__ = "tags"

    # Define the attributes in the table and their unique characteristics (data type, whether or not nullable, primary keys)

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), unique = True, nullable = False)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable = False)

    # We also create a relationship with our Store Model (need two ends to the relationship)
    store = db.relationship("StoreModel", back_populates="tags") 

    # Finally we create a relationship with our Items Model (many to many)
    items = db.relationship("ItemModel", back_populates="tags", secondary="items_tags")