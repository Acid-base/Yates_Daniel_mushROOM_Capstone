from typing import Dict, Any
import jsonschema
from jsonschema import validate as json_validate
from pydantic import BaseModel


def to_json_schema(model_class: type[BaseModel]) -> Dict[str, Any]:
    """Convert a Pydantic model to JSON schema."""
    return model_class.model_json_schema()


def validate_data(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.

    Args:
        data: Dictionary containing the data to validate
        schema: JSON schema to validate against

    Returns:
        bool: True if validation succeeds, False otherwise
    """
    try:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            schema = to_json_schema(schema)
        json_validate(instance=data, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError:
        return False
    except Exception:
        return False
