from typing import List, Dict
from app.models.enums import UserRole

# Access Tier Mapping based on Institutional Security Hierarchy
# PUBLIC: only PUBLIC-tier documents
# STUDENT: PUBLIC + STUDENT-tier documents
# LECTURER: PUBLIC + STUDENT + LECTURER-tier documents
# ADMIN: PUBLIC + STUDENT + LECTURER + ADMIN-tier documents (all tiers)

ROLE_ACCESS_TIERS: Dict[UserRole, List[UserRole]] = {
    UserRole.PUBLIC: [UserRole.PUBLIC],
    UserRole.STUDENT: [UserRole.PUBLIC, UserRole.STUDENT],
    UserRole.LECTURER: [UserRole.PUBLIC, UserRole.STUDENT, UserRole.LECTURER],
    UserRole.ADMIN: [UserRole.PUBLIC, UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN],
}

def get_access_tiers_for_role(role: UserRole) -> List[UserRole]:
    """Retrieve the list of allowed document access tiers for a given user role."""
    return ROLE_ACCESS_TIERS.get(role, [UserRole.PUBLIC])
