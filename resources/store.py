from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Import database
from db import db
from models import StoreModel

# Import Schema
from schemas import StoreSchema

blp = Blueprint("stores", __name__, description = "Operations on stores")

@blp.route("/store/<int:store_id>")
class Store(MethodView):
    @blp.response(200,StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store

    def delete(self, store_id):
        # Flask SQLAlchemy allows us to perform a get query on our StoreModel
        # This gets the store data associated with store_id or if it does not exist will create a 404 error
        store = StoreModel.query.get_or_404(store_id)

        # We then remove the store from the database
        db.session.delete(store)
        # Write to database (save to disk)
        db.session.commit()

        # We then return a message to the client, due to the query we will also get a 202 success message
        return {"message": "Store deleted."}

@blp.route("/store")
class StoreList(MethodView):
    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()

    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        # Exception if it would create a database inconsistency (i.e. a duplicate store value)
        except IntegrityError:
            abort(
                400,
                message="A store with that name already exists.",
            )
        except SQLAlchemyError:
            abort(500, message="An error occurred creating the store.")

        return store