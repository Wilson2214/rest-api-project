from marshmallow import Schema, fields

# Create Schema for validating incoming data and turning outgoing data into valid datasets
# Validation will be handled by marshmallow

# load_only: only when receiving data from client
# dump_only: only when sending data to client

# Schema ignoring store
class PlainItemSchema(Schema):
    id = fields.Int(dump_only=True) # Will not include in the json payload, not used for validation, sent to user
    name = fields.Str(required=True) # Will be required in payload
    price = fields.Float(required=True) # Confirms price will be a numeric float

class PlainStoreSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)

class PlainTagSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()

# Schema for updating an item
class ItemUpdateSchema(Schema):
    name = fields.Str()
    price = fields.Float()
    #store_id = fields.Int() # added to allow us to use put request to update item that does not exist

# Schema including store (inherits from PlainItemSchema so has to come after PlainStoreSchema)
class ItemSchema(PlainItemSchema):
    store_id = fields.Int(required=True, load_only=True)
    store = fields.Nested(PlainStoreSchema(), dump_only=True)
    tags = fields.List(fields.Nested(PlainTagSchema()), dump_only=True)

class StoreSchema(PlainStoreSchema):
    items = fields.List(fields.Nested(PlainItemSchema()), dump_only=True)
    tags = fields.List(fields.Nested(PlainTagSchema()), dump_only=True)

class TagSchema(PlainTagSchema):
    store_id = fields.Int(load_only=True)
    store = fields.Nested(PlainStoreSchema(), dump_only=True)
    items = fields.List(fields.Nested(PlainItemSchema()), dump_only=True)

class TagAndItemSchema(Schema):
    message = fields.Str()
    item = fields.Nested(ItemSchema)
    tag = fields.Nested(TagSchema)

# Schema for users
class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    # never save the password or send this data
    password = fields.Str(required=True, load_only=True)

class UserRegisterSchema(UserSchema):
    email = fields.Str(required=True)