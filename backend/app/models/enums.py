import enum

class UserRole(str, enum.Enum):
    PUBLIC = "PUBLIC"
    STUDENT = "STUDENT"
    LECTURER = "LECTURER"
    ADMIN = "ADMIN"

class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
