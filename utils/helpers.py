# helpers.py
cat > utils/helpers.py << 'EOF'
from datetime import datetime
import string
import random

def format_time_ago(timestamp):
    """Format timestamp to time ago string"""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def generate_random_string(length=10):
    """Generate random string"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def format_currency(amount):
    """Format currency with rupee symbol"""
    return f"₹{amount:,.2f}"
EOF

