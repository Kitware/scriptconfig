"""
Helpers related to exceptions
"""


def add_exception_note(ex, note, force_legacy=False):
    """
    Add unstructured information to an exception.

    If PEP 678 is available (i.e. on Python >= 3.11), use it, otherwise create
    a new exception based on the old one with an updated note.

    Args:
        ex (BaseException): the exception to modify
        note (str): extra information to append to the exception
        force_legacy (bool): for testing

    Returns:
        BaseException: modified exception

    Example:
        >>> from scriptconfig.util import util_exception
        >>> ex = Exception('foo')
        >>> new_ex = util_exception.add_exception_note(ex, 'hello world', force_legacy=False)
        >>> print(new_ex)
        >>> new_ex = util_exception.add_exception_note(ex, 'hello world', force_legacy=True)
        >>> print(new_ex)
    """
    if not force_legacy and hasattr(ex, 'add_note'):
        # Requires python.311 PEP 678
        ex.add_note(note)
        return ex
    else:
        return type(ex)(str(ex) + chr(10) + note)
