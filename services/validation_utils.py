
import re
from typing import Dict, List, Any, Tuple


def validate_email(email: str) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate email format using regex pattern.
    
    Args:
        email: Email string to validate
        
    Returns:
        Tuple of (is_valid: bool, errors: dict with field errors)
        - is_valid: True if email format is valid, False otherwise
        - errors: Dictionary with 'email' key containing list of error messages
        
    Example:
        >>> is_valid, errors = validate_email("user@example.com")
        >>> is_valid
        True
        >>> errors
        {}
        
        >>> is_valid, errors = validate_email("invalid-email")
        >>> is_valid
        False
        >>> errors
        {'email': ['Invalid email format']}
    """
    errors = {}
    
    # Email regex pattern - matches standard email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email or not isinstance(email, str):
        errors['email'] = ['Email is required and must be a string']
        return False, errors
    
    email = email.strip()
    
    if not re.match(email_pattern, email):
        errors['email'] = ['Invalid email format']
        return False, errors
    
    return True, {}


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate that all required fields are present and non-empty in the data object.
    
    Args:
        data: Dictionary containing the data to validate
        required_fields: List of field names that are required
        
    Returns:
        Tuple of (is_valid: bool, errors: dict with field errors)
        - is_valid: True if all required fields are present and non-empty, False otherwise
        - errors: Dictionary mapping field names to lists of error messages
        
    Example:
        >>> data = {'name': 'John', 'email': 'john@example.com'}
        >>> is_valid, errors = validate_required_fields(data, ['name', 'email'])
        >>> is_valid
        True
        >>> errors
        {}
        
        >>> data = {'name': '', 'email': 'john@example.com'}
        >>> is_valid, errors = validate_required_fields(data, ['name', 'email'])
        >>> is_valid
        False
        >>> errors
        {'name': ['Field is required and cannot be empty']}
    """
    errors = {}
    
    if not isinstance(data, dict):
        return False, {'data': ['Data must be a dictionary']}
    
    for field in required_fields:
        value = data.get(field)
        
        # Check if field is missing or empty
        if value is None or (isinstance(value, str) and not value.strip()):
            if field not in errors:
                errors[field] = []
            errors[field].append('Field is required and cannot be empty')
    
    return len(errors) == 0, errors


def validate_user(user_data: Dict[str, Any], operation: str = 'create') -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate user data for create or update operations.
    
    Performs both email format validation and required-field validation
    based on the operation type.
    
    Args:
        user_data: Dictionary containing user data to validate
        operation: Type of operation - 'create' or 'update'
                  'create' requires all fields, 'update' is more lenient
        
    Returns:
        Tuple of (is_valid: bool, errors: dict with field errors)
        - is_valid: True if all validations pass, False otherwise
        - errors: Dictionary mapping field names to lists of error messages
        
    Example:
        >>> user_data = {'name': 'John Doe', 'email': 'john@example.com'}
        >>> is_valid, errors = validate_user(user_data, 'create')
        >>> is_valid
        True
        >>> errors
        {}
        
        >>> user_data = {'name': 'John Doe', 'email': 'invalid-email'}
        >>> is_valid, errors = validate_user(user_data, 'create')
        >>> is_valid
        False
        >>> errors
        {'email': ['Invalid email format']}
    """
    all_errors = {}
    
    # Define required fields based on operation type
    if operation == 'create':
        required_fields = ['name', 'email']
    else:  # update
        required_fields = []  # Updates can be partial
    
    # Validate required fields
    fields_valid, field_errors = validate_required_fields(user_data, required_fields)
    all_errors.update(field_errors)
    
    # Validate email format if email field is present
    if 'email' in user_data and user_data['email']:
        email_valid, email_errors = validate_email(user_data['email'])
        if not email_valid:
            all_errors.update(email_errors)
    elif operation == 'create' and 'email' not in all_errors:
        # Email is required for create operations
        all_errors['email'] = ['Email is required']
    
    return len(all_errors) == 0, all_errors


def format_validation_errors(errors: Dict[str, List[str]]) -> str:
    """
    Format validation errors into a human-readable string.
    
    Args:
        errors: Dictionary mapping field names to lists of error messages
        
    Returns:
        Formatted error string suitable for user-facing error messages
        
    Example:
        >>> errors = {'email': ['Invalid email format'], 'name': ['Field is required']}
        >>> format_validation_errors(errors)
        'email: Invalid email format. name: Field is required.'
    """
    if not errors:
        return ""
    
    error_messages = []
    for field, messages in errors.items():
        field_errors = ". ".join(messages)
        error_messages.append(f"{field}: {field_errors}")
    
    return ". ".join(error_messages) + "."

