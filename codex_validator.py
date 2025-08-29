from pydantic import BaseModel, ValidationError

class Credential(BaseModel): user: str; credential: str

class OverrideRequest(BaseModel): requestor: str; action: str; target: str

def validate_payload(schema, payload):
    try:
        validated = schema(**payload)
        return {"valid": True, "data": validated.dict()}
    except ValidationError as e:
        return {"valid": False, "errors": e.errors()}
