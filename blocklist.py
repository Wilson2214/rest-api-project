"""
blocklist.py

This file just contains the blocklist of the JWT tokens. It will be imported by
app and the logout resource so that tokens can be added to the blocklist when the
user logs out.
"""

BLOCKLIST = set()

# This is a python set, when the app resets, the blocklist is deleted
# This is not the best option for storing blocklist
# Maximum performance would be to use Redis or other database option