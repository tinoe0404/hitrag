import enum

class UserRole(str, enum.Enum):
    PUBLIC = "PUBLIC"
    STUDENT = "STUDENT"
    LECTURER = "LECTURER"
    ADMIN = "ADMIN"

class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"          # Keep for backward compatibility
    UPLOADED = "UPLOADED"        # Initial upload status
    PROCESSING = "PROCESSING"    # Keep for backward compatibility
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    CLEANING = "CLEANING"
    CLEANED = "CLEANED"
    CHUNKING = "CHUNKING"
    CHUNKED = "CHUNKED"
    EMBEDDING = "EMBEDDING"
    EMBEDDED = "EMBEDDED"
    EXT_FAILED = "EXT_FAILED"
    EMB_FAILED = "EMB_FAILED"
    EMB_READY = "EMB_READY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
