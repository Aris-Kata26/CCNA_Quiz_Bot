#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os  # Provides functions to interact with the operating system.
import sys  # Provides access to system-specific parameters and functions.

def main():
    """Run administrative tasks."""
    # Set the default settings module for the Django project.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ccnaquizbot.settings')
    
    try:
        # Import the function to execute Django commands from the command line.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Raise an error if Django is not installed or the environment is not set up correctly.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Execute the command-line utility with the provided arguments.
    execute_from_command_line(sys.argv)

# Entry point of the script.
if __name__ == '__main__':
    main()
