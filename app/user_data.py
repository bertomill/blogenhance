import json
import os
from werkzeug.security import generate_password_hash

# Path to the JSON file that will store user data
USER_DATA_FILE = os.path.join(os.path.dirname(__file__), 'user_data.json')

def load_users():
    """
    Load all users from the JSON data file.
    If the file doesn't exist, create it with an empty users list.
    
    Returns:
        list: List of user dictionaries
    """
    if not os.path.exists(USER_DATA_FILE):
        # Create an initial file with an admin user if it doesn't exist
        initial_data = {
            'users': [
                {
                    'id': '1',
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'password_hash': generate_password_hash('adminpassword'),
                    'profile': {
                        'personality': 'thoughtful and analytical',
                        'writing_style': 'clear and conversational',
                        'expertise': 'digital marketing and content strategy',
                        'background': 'Several years of experience in content creation and blog management'
                    }
                }
            ]
        }
        save_user_data(initial_data)
        return initial_data['users']
    
    try:
        with open(USER_DATA_FILE, 'r') as f:
            data = json.load(f)
            return data.get('users', [])
    except (json.JSONDecodeError, FileNotFoundError):
        # If the file is corrupted or can't be read, create a new one
        return []

def save_user_data(data):
    """
    Save user data to the JSON file.
    
    Args:
        data (dict): Dictionary containing user data to save
    """
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def save_users(users):
    """
    Save the list of users to the user data file.
    
    Args:
        users (list): List of user dictionaries to save
    """
    data = {'users': users}
    save_user_data(data)

def get_next_user_id(users):
    """
    Generate a new unique user ID.
    
    Args:
        users (list): Current list of users
        
    Returns:
        str: Next available user ID
    """
    if not users:
        return '1'
    
    # Find the maximum ID and increment it
    max_id = max(int(user.get('id', 0)) for user in users)
    return str(max_id + 1) 