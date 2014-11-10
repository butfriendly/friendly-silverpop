
class Error(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, msg, code=None):
        self.msg = msg
        self.code = code

    def __str__(self):
        return '%s (%r)' % (self.msg, self.code)


class EngageError(Error):
    pass


class SessionIsExpiredOrInvalidError(EngageError):
    pass


class RecipientAlreadyExistsError(EngageError):
    pass


class UnsupportedExportTypeError(EngageError):
    pass


class UnsupportedExportFormatError(EngageError):
    pass