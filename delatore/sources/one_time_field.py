from typing import Any


class OneTimeField:
    __value = None

    def __init__(self, value: Any = None):
        self.__value = value

    def __get__(self, instance, owner):
        val = self.__value
        self.__value = None
        return val

    def __set__(self, instance, value):
        self.__value = value
