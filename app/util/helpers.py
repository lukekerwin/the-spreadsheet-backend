"""
Helper Utilities

Common utility functions for database queries and parameter validation.
"""

from sqlalchemy import select, func

# ============================================
# DATABASE HELPERS
# ============================================

async def get_count(session, model, filters):
    """
    Get count of rows matching the given filters.
    
    Args:
        session: AsyncSession database session
        model: SQLAlchemy model class
        filters: List of filter conditions
        
    Returns:
        int: Count of matching rows
    """
    count_stmt = select(func.count()).select_from(model).where(*filters)
    total_result = await session.execute(count_stmt)
    return total_result.scalar() or 0

# ============================================
# VALIDATION HELPERS
# ============================================

def validate_param(param, value, allowed_values=[], gt=None, lt=None) -> bool:
    """
    Validate a parameter against constraints.
    
    Args:
        param: Parameter name (for error messages)
        value: Value to validate
        allowed_values: List of allowed values (empty = any)
        gt: Value must be greater than this
        lt: Value must be less than this
        
    Returns:
        bool: True if valid, False otherwise
    """
    if allowed_values and value not in allowed_values:
        return False
    if gt and value <= gt:
        return False
    if lt and value >= lt:
        return False
    return True