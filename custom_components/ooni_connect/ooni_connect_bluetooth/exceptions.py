class BaseError(Exception):
    pass


class DecodeError(BaseError):
    pass


class WriteFailed(BaseError):
    pass
