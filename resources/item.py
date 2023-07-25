from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required, get_jwt

# Import database and models for database
from db import db
from models import ItemModel

# Import Schema
from schemas import ItemSchema, ItemUpdateSchema

# A blueprint is an object that allows defining application functions without requiring an application object ahead of time
# Blueprints record operations to be executed later when you register them on an application (blp arguments)
# This is required to create initial blueprint
blp = Blueprint("items", __name__, description = "Operations on items")

# We need an individual route for each endpoint that we will be working with

# Decorator to determine the route in which methodviews will call to
@blp.route("/item/<int:item_id>")
# Create a class which inherits from MethodView meaning it contains the methods to work with API (get, post, pull, etc)
class Item(MethodView):
    # Add authentication: user must be created, then have a token created with login endpoint
    @jwt_required()
    # Get request returns data, validated by marshmallow using the response decorator (200 meaning OK)
    @blp.response(200, ItemSchema)
    # Define the get request per the the MethodView against the decorated route
    # self represents the instance of class. This handy keyword allows you to access variables, attributes, and methods of a defined class in Python.
    # item_id is included as a parameter to this request because it is defined in <> within the route
    def get(self, item_id):
        # Flask SQLAlchemy allows us to perform a get query on our ItemModel
        # If the get query fails we get a 404 error
        item = ItemModel.query.get_or_404(item_id) # Retrieves item by primary key or will give 404 error
        # Return the item object that is created
        return item

    # Add authentication: user must be created, then have a token created with login endpoint
    @jwt_required()
    # Define the delete request per the MethodView against the decorated route
    def delete(self, item_id):

        # Use JWT Claims to confirm user is an admin
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message = "Admin privilege required.")

        # Flask SQLAlchemy allows us to perform a get query on our ItemModel
        # This gets the item data associated with item_id or if it does not exist will create a 404 error
        item = ItemModel.query.get_or_404(item_id)

        # We then remove the item from the database
        db.session.delete(item)
        # Write to database (save to disk)
        db.session.commit()

        # We then return a message to the client, due to the query we will also get a 202 success message
        return {"message": "Item deleted."}

    # Because a put request includes a json payload (argument in body), 
    # we add blp.argument to enforce schema for this particular json request
    @blp.arguments(ItemUpdateSchema)
    # We then have the same response validation decorator
    @blp.response(200, ItemSchema)
    # Defining a put request
    def put(self, item_data, item_id):
        # item_data is the json data provided in the post request from client
        # item_id is included as a parameter to this request because it is defined in <> within the route
        # Perform a get query using the item_id to get the ItemModel
        # We removed the get_or_404 to allow for the if statement to run if the get_or_404 error fails
        item = ItemModel.query.get(item_id)
        # If item exists we update in the database, otherwise we add it
        if item:
            # Update the ItemModel price with the json payloads price
            item.price = item_data["price"]
            # Update the ItemModel name with the json payloads name
            item.name = item_data["name"]
        else:
            # If it does not exist, we add it using the item_data and assign the id as the item_id that is passed
            item = ItemModel(id=item_id, **item_data)

        # Add to database (not written)
        db.session.add(item)
        # Write to database (save to disk)
        db.session.commit()

        # We then return the item model with a 201 success message to show what was inserted to the client
        return item

# Decorator to determine the route in which methodviews will call to
@blp.route("/item")
class ItemList(MethodView):
    # Add authentication: user must be created, then have a token created with login endpoint
    @jwt_required()
    # Get request returns data, validated by marshmallow using the response decorator (200 meaning OK)
    # Many set to True because we are returning multiple items
    @blp.response(200, ItemSchema(many=True)) 
    # Defining a get request
    def get(self):
        # Flask SQLAlchemy allows us to perform an all query on our ItemModel
        # all method will go through every item in list where list was created by selecting many=True in ItemSchema
        return ItemModel.query.all()

    # Add in authentication
    # Cannot call this endpoint unless jwt provided
    # Adding fresh = True means we need a fresh token, not a refresh token
    @jwt_required(fresh=True)
    # Again, we enforce schema for the incoming argument request (json payload)
    @blp.arguments(ItemSchema)
    # And enforce the schema for the response
    @blp.response(201, ItemSchema)
    # Defining a post request
    def post(self, item_data):
        # item_data is the json data provided in the post request from client
        # This gets passed to the ItemModel class as key word arguments (data validation) which creates the item for the database
        # This just creates the item model, it does not add it to the database or check its uniqueness
        item = ItemModel(**item_data)

        # We must then attempt to add it to the database
        try:
            # Add to database (not written)
            db.session.add(item)
            # Write to database (save to disk)
            db.session.commit()
        # Unless there is a generic error with inserting into the database
        # In our case most likely the error is that we did not supply a store_id in the item_data json which is required 
        # per ItemModel class which notes store_id nullable = False
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the item.")

        # We then return the item model with a 201 success message to show what was inserted to the client
        return item