from .base import BaseEnum


class Status(BaseEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"