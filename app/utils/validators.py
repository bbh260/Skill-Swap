import re

def validate_email(email):
    """Validate email format using regex"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_password(password):
    """Validate password strength - minimum 6 characters"""
    return len(password) >= 6

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present and not empty"""
    missing_fields = []
    for field in required_fields:
        if not data.get(field) or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)
    return missing_fields

def sanitize_string(value, max_length=None):
    """Sanitize string input by trimming whitespace and limiting length"""
    if not isinstance(value, str):
        return value
    
    sanitized = value.strip()
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized
