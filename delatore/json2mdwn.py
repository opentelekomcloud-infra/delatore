import json
import re


def backtick_values(data):
    """Escape json values with backticks

    To define your behaviour, implement `__md__` method in your class
    """
    if hasattr(data, "__md__"):
        return data.__md__()
    if isinstance(data, dict):
        return {f"{key} ".replace("_", " ").title(): backtick_values(data[key]) for key in data}
    if isinstance(data, list):
        return [backtick_values(item) for item in data]
    return f"`{data}`"


__MARKS = re.compile(r"[{}\",\[\]]")


def convert(data):
    """Convert dict or list to nice-looking telegram markdown"""
    formatted = __MARKS.sub("", json.dumps(backtick_values(data), separators=("", ":    "), indent=4))
    formatted = "\n".join(line[4:].rstrip() for line in formatted.split("\n") if line.rstrip() != "")
    return formatted
