import enum

class UserRole(str, enum.Enum):
    PUBLIC = "PUBLIC"
    STUDENT = "STUDENT"
    LECTURER = "LECTURER"
    ADMIN = "ADMIN"

class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
