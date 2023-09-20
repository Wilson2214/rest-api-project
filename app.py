from flask import Flask
from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import os
import redis

from dotenv import load_dotenv
from rq import Queue

from db import db
import models
from blocklist import BLOCKLIST

from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint

# Define the app with various config settings and pointers to files within this directory
def create_app(db_url=None):
    app = Flask(__name__)

    # Load environment file to allow for loading of postgresql database url
    load_dotenv()

    # Setup Queue
    connection = redis.from_url(
        os.getenv("REDIS_URL")
    )
    app.queue = Queue("emails", connection=connection)

    # App Settings
    # Hidden exceptions in flask should be brought into main app
    app.config["PROPAGATE_EXCEPTIONS"] = True

    # For documentation
    app.config["API_TITLE"] = "Stores REST API"

    # Can be updated as changes are made
    app.config["API_VERSION"] = "v1"

    # Standard for documentation
    app.config["OPENAPI_VERSION"] = "3.0.3"

    # Root of API
    app.config["OPENAPI_URL_PREFIX"] = "/"

    # Automatically created documentation of API
    # DOCUMENTATION AT: http://127.0.0.1:5005/swagger-ui
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # Connection String for Database
    # Option for Development: sqllite:///data.db (Data will be stored in data.db file)
    # Option for Production: uses DATABASE_URL from .env currently pointing to ElephantSQL
    # Will eventually migrate to PostGres
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")

    # Extra sqlalchemy settings
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize flask sqlalchemy extension
    db.init_app(app)

    # Add migration
    migrate = Migrate(app,db)

    # Link smorest to app
    api = Api(app)

    # Create instance of jwt for app to handle authentification
    # Need to create a secret key so when user sends JWT to identify themselves, app can verify it is authentic
    # Normally would generate key (using secrets module like secrets.SystemRandom().getrandbits(128) to use as secret key)
    app.config["JWT_SECRET_KEY"] = "jose"
    jwt = JWTManager(app)

    # See if an existing token is in blocklist and therefore means access should not be granted
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST

    # If above function is returned true, the following error is returned
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "The token has been revoked.", "error": "token_revoked"}
            ),
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "The token is not fresh.",
                    "error": "fresh_token_required",
                }
            ),
            401,
        )

    # This portion is not often used, but can be added
    # Allows you to add extra info to jwt when being created
    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        # This is just noting that the first user in the database is the admin, and no others
        # Preferred method would be to look in database (which contains this info) and confirm user is admin
        if identity == 1:
            return {"is_admin": True}
        return {"is_admin": False}

    # Add functions for error handling authentication in app
    # Returns error when JWT is expired
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token has expired.", "error": "token_expired"}),
            401,
        )

    # Returns error when JWT is invalid
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    # Returns error when JWT is missing
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401,
        )

    # Now handled by flask-migrate
    # # Create tables if they do not exist in the database
    # with app.app_context():
    #     db.create_all()

    # Register blueprints in resources so that they will be used by the API
    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    return app
