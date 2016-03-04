# Copyright 2014 MathWorks, Inc.

# NOTE: Trailing ones (if any) are removed prior to comparing the sizes


class SizeError(Exception):
    """
    SizeError is thrown when:
        1. Both Initializer and Size is given in the constructor
        2. Initializer is a nested sequence
        3. Size, given in the constructor, does not exactly match
         the size of the nested sequence
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


class ShapeError(Exception):
    """
    ShapeError is thrown when:
        1. Both Initializer and Size is given in the constructor
        2. Number of elements in the initializer do not match the total
        number of expected elements in the size
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value