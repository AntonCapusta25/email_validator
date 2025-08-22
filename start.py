#!/usr/bin/env python3
"""
Simple startup script for email validator
IMPORTANT: This avoids naming conflicts with email-validator package!
"""

import os
import sys

def main():
    """Main startup function"""
    # Check if running in web mode
    if os.environ.get('WEB_MODE', 'false').lower() == 'true':
        # Import and run Flask app
        from app import app
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        # Run CLI version - import from renamed validator module
        from validator import interactive_validator
        interactive_validator()

if __name__ == '__main__':
    main()
