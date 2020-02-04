import jsonschema
from jsonschema import validate

schema = {
    'description': 'Core schema for unified JSON',
    'type': 'object',
    'properties': {
        'source': {
            'type': 'string'
        },
        'status_list': {
            'type': 'array'
        },
        'error': {
            'type': 'string'
        }
    }
}


def test_json_schema(source_data):
    _src, (_, expected) = source_data
    assert validate(instance=expected, schema=schema) is not jsonschema.exceptions.SchemaError
