import uuid

def is_valid_guid(guid_str):
    """Utility to check valid Guid."""
    try:
        # Attempt to create a UUID object
        uuid_obj = uuid.UUID(guid_str, version=4)
        # Check if the string representation matches the UUID object
        return str(uuid_obj) == guid_str
    except ValueError:
        return False