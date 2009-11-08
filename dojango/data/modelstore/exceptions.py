""" Django ModelStore exception classes
"""

__all__ = ('MethodException', 'FieldException',
            'StoreException', 'ServiceException')

class MethodException(Exception):
    """ Raised when an error occurs related to a custom
        method (Method, ObjectMethod, etc.) call
    """
    pass

class FieldException(Exception):
    """ Raised when an error occurs related to a custom
        StoreField definition
    """
    pass

class StoreException(Exception):
    """ Raised when an error occurs related to a
        Store definition
    """

class ServiceException(Exception):
    """ Raised when an error occurs related to a custom
        Service definition or servicemethod call
    """
