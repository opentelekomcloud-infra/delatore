from delatore.json2mdwn import convert


def test_backtick():
    data = {
        "item": "value",
        "list": [
            "a",
            "b"
        ],
        "dict": {
            "item": "value"
        }
    }
    expected = """Item :    `value`
List :
    `a`
    `b`
Dict :
    Item :    `value`"""
    assert convert(data) == expected
