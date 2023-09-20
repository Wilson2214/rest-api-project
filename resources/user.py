from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, create_refresh_token, get_jwt_identity
from sqlalchemy import or_

from db import db
from models import UserModel
from schemas import UserSchema, UserRegisterSchema
from blocklist import BLOCKLIST

from tasks import send_user_registration_email
from flask import current_app

blp = Blueprint("Users", "users", description="Operations on users")

# Create user login endpoint
@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema) # Receiving a username and password
    def post(self, user_data):
        # Filter the database for the username to get user which will represent username / password
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        # Confirm that the password provided in user_data is the same as password in database
        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            # If matches, return an access token
            access_token = create_access_token(identity=user.id, fresh=True)
            # Create refresh token
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

        abort(401, message="Invalid credentials.")

# Create user logout endpoint
@blp.route("/logout")
class UserLogout(MethodView):
    # Add authentication: user must be created, then have a token created with login endpoint
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"] # alternatively could run get_jwt().get("jti")
        # Add jti to blocklist (i.e. the key to blocklist for comparison)
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}, 200

# Create user refresh endpoint
@blp.route("/refresh")
class TokenRefresh(MethodView):
    # Authentification only requires a refresh token, not a fresh access_token
    @jwt_required(refresh=True)
    def post(self):
        # Identify user from existing access_key
        current_user = get_jwt_identity()
        # Create a new non-fresh token
        new_token = create_access_token(identity=current_user, fresh=False)
        # Make it clear that when to add the refresh token to the blocklist will depend on the app design
        # If we try to get a second non-fresh token, it will be blocklisted. This allows for one non-fresh to every refresh
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token": new_token}, 200

# Create register endpoint
@blp.route("/register")
# Create a User Registration class inheriting from MethodView which comes from flask.views
class UserRegister(MethodView):
    # Define the request and assign the schema with a decorator (in this case the UserSchema from schemas.py)
    @blp.arguments(UserRegisterSchema)
    # Define a post request accepting data via the UserSchema (includes id, username, and password via user_data i.e. json payload)
    def post(self,user_data):
        # Add a check to see if the user_data payload username is already in the database for registration
        if UserModel.query.filter(
            or_(
                UserModel.username == user_data["username"],
                UserModel.email == user_data["email"],
                )
        ).first():
            # If it is abort
            abort(409, message="A user with that username already exists.")

        # To create an object to be entered into the database model, assign the username and password
        # This is a manual creation instead of using something like ItemModel(**item_data) where we directly pass user_data
        user = UserModel(
            username=user_data["username"],
            email=user_data["email"],
            # Use the hash functionality to hide the password prior to saving
            password=pbkdf2_sha256.hash(user_data["password"])
        )

        try:
            # Add to database (not written)
            db.session.add(user)
            # Write to database (save to disk)
            db.session.commit()
            # Send message upon registration
            current_app.queue.enqueue(send_user_registration_email, user.email, user.username)
            
        # Unless there is a generic error with inserting into the database
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the item.")

        # Return a message to the client
        return {"message": "User created successfully."}, 201

# Define our get and delete method
@blp.route("/user/<int:user_id>")
class User(MethodView):
    """
    This resource can be useful when testing our Flask app.
    We may not want to expose it to public users, but for the
    sake of demonstration in this course, it can be useful
    when we are manipulating data regarding the users.
    """

    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted."}, 200