from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

# Import database
from db import db
from models import TagModel, StoreModel, ItemModel

# Import Schema
from schemas import TagSchema
from schemas import TagAndItemSchema

blp = Blueprint("tags", __name__, description = "Operations on tags")

# Decorator to determine the route in which methodviews will call to
@blp.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):
    # Get request returns data, validated by marshmallow using the response decorator (200 meaning OK)
    # Many set to True because we are returning multiple items
    @blp.response(200, TagSchema(many=True))
    # Request is providing a store_id to show all associated tags which gets passed to the GET request
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        # Return the StoreModel showing all tags
        return store.tags.all()

    # We enforce schema for the incoming argument request (json payload)
    @blp.arguments(TagSchema)
    # Goal here is to create a tag linked to a store (we are providing store_id)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        # Can check if the tag already exists in the store using filters and abort
        if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_data["name"]).first():
            abort(400, message="A tag with that name already exists in that store.")

        # Creates a TagModel and adds the store_id passed in the request
        tag = TagModel(**tag_data, store_id=store_id)

        # Add to the database
        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(
                500,
                message=str(e), #Return the exception provided by SQLAlchemyError
            )

        return tag

# Decorator to determine the route in which methodviews will call to
@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @blp.response(201, TagSchema)
    # Request to link an item in a store with a tag from the same store
    def post(self, item_id, tag_id):
        # Get both the item and the tag (confirm that they exist)
        # The tag and item are created in previous requests, this is tot just link the item and tag
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        # Add a check to confirm that tag and item have the same store
        if item.store.id != tag.store.id:
            abort(400, message="Make sure item and tag belong to the same store before linking.")

        # Simply append the tag to the item in the secondary table
        item.tags.append(tag)

        # Add this item to the items table with the new tag appended
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the tag.")

        # Return information about the new tag created
        return tag

    @blp.response(200, TagAndItemSchema)
    # Request to unlink an item in a store with a tag from the same store
    def delete(self, item_id, tag_id):
        # Get both the item and the tag (confirm that they exist)
        # The tag and item are created in previous requests, this is tot just link the item and tag
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        # Add a check to confirm that tag and item have the same store
        if item.store.id != tag.store.id:
            abort(400, message="Make sure item and tag belong to the same store before unlinking.")

        # Instead of appending a tag to the item, we remove the tag from the item
        item.tags.remove(tag)

        # Add this updated item to the database without the ta
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the tag.")

        # Let client know the tag was succesfully removed
        return {"message": "Item removed from tag", "item": item, "tag": tag}

# Decorator to determine the route in which methodviews will call to
@blp.route("/tags/<int:tag_id>")
class Tag(MethodView):
    # Request to get information about an individual tag (store it is associated with)
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    # Add decorators for various responses to a delete call
    # This is a succesful delete, but it deletes a tag when there is no item associated to it
    @blp.response(
        202,
        description="Deletes a tag if no item is tagged with it.",
        example={"message": "Tag deleted."},
    )
    # Alternate Response to the initial response laid out
    # Error if the tag is not found
    @blp.alt_response(404, description="Tag not found.")
    # Error if tag to be deleted is assigned to an item, the tag must not be associated with an item to be deleted
    @blp.alt_response(
        400,
        description="Returned if the tag is assigned to one or more items. In this case, the tag is not deleted.",
    )
    # Request is to delete a tag
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)

        # Confirm the tag is not associated with an item (checking backfilled list of items associated with tag)
        if not tag.items:
            # Delete the tag and remove from database
            db.session.delete(tag)
            db.session.commit()
            return {"message": "Tag deleted."}
        abort(
            400,
            message="Could not delete tag. Make sure tag is not associated with any items, then try again.",
        )