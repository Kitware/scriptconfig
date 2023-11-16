class class_or_instancemethod(classmethod):
    """
    A decorator that allows a method to behave as a class or instance method.

    The user is responsible for testing if the first arugment is an instance of
    the class or the class itself. This is can be done by using
    ``isinstance(..., type)``. More explicitly, if the first argument of the
    decorated function is ``self_or_cls``, then ``isinstance(self_or_cls,
    type)`` returns True if the function is behaving as a classmethod and False
    if it is an instance method.

    This code is derived from [SO28237955]_.

    References:
        .. [SO28237955] https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod

    Example:
        >>> class X:
        ...     @class_or_instancemethod
        ...     def foo(self_or_cls):
        ...         if isinstance(self_or_cls, type):
        ...             return f"bound to the class"
        ...         else:
        ...             return f"bound to the instance"
        >>> print(X.foo())
        bound to the class
        >>> print(X().foo())
        bound to the instance
    """
    def __get__(self, instance, owner=None):
        """
        Descriptor method

        References:
            https://docs.python.org/3/reference/datamodel.html#object.__get__
        """
        if instance is None:
            descr_get = super().__get__
        else:
            descr_get = self.__func__.__get__
        return descr_get(instance, owner)


# class hybridmethod:
#     """
#     Dispatch alternative to :class:`class_or_instancemethod`.

#     TODO:
#         Can this be cleaned up at all? Need docs explaining how this works.

#     Example:
#         >>> from scriptconfig.util.util_class import *  # NOQA
#         >>> class X:
#         ...     @hybridmethod
#         ...     def bar(cls):
#         ...         return f"bound to the class, {cls}"
#         ...     @bar.instancemethod
#         ...     def bar(self):
#         ...         return f"bound to the instance, {self}"
#         ... #
#         ... assert isinstance(X.__dict__['bar'], hybridmethod)
#         >>> print(X.bar())
#         >>> print(X().bar())
#         "bound to the class, <class '__main__.X'>"
#         'bound to the instance, <__main__.X object at 0x10a010f70>'

#     """
#     def __init__(self, fclass, finstance=None, doc=None):
#         print(f'CONSTRUCT hybridmethod with fclass={fclass}, finstance={finstance} doc={doc}')
#         self.fclass = fclass
#         self.finstance = finstance
#         self.__doc__ = doc or fclass.__doc__
#         # support use on abstract base classes
#         self.__isabstractmethod__ = bool(
#             getattr(fclass, '__isabstractmethod__', False)
#         )

#     def classmethod(self, fclass):
#         self_cls = type(self)
#         print(f'CALL classmethod with self_cls={self_cls}')
#         return self_cls(fclass, self.finstance, None)

#     def instancemethod(self, finstance):
#         self_cls = type(self)
#         print(f'CALL instancemethod with self_cls={self_cls}')
#         return self_cls(self.fclass, finstance, self.__doc__)

#     def __get__(self, instance, owner=None):
#         print('INVOKE hybridmethod.__get__')
#         print(f'owner={owner}')
#         print(f'instance={instance}')
#         if instance is None or self.finstance is None:
#             # either bound to the class, or no instance method available
#             return self.fclass.__get__(owner, None)
#         return self.finstance.__get__(instance, owner)
