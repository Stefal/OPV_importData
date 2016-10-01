from functools import wraps

def singleton(cls):
    """make the class as singleton"""
    @wraps(cls)
    def fct():
        """
        create a new object if no one exit
        """
        if not fct.instance:
            fct.instance = cls()
        return fct.instance
    fct.instance = None

    return fct
