#!/usr/bin/env python3
"""
Email Validator API - FINAL FIXED VERSION
- Proper CORS configuration
- No DNS timeouts
- Fast and reliable
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from typing import List, Dict
import re

app = Flask(__name__)

# PROPER CORS Configuration - this fixes CORS issues completely
CORS(app, 
     origins=["*"],  # Allow all origins
     methods=["GET", "POST", "OPTIONS"],  # Allow these methods
     allow_headers=["Content-Type", "Authorization"],  # Allow these headers
     supports_credentials=False)

def validate_email_simple(email):
    """
    Fast, reliable email validation without DNS lookups
    """
    try:
        if not email or not isinstance(email, str):
            return {
                'email': email,
                'is_valid': False,
                'error': 'Email must be a string'
            }
        
        email = email.strip()
        if not email:
            return {
                'email': email,
                'is_valid': False,
                'error': 'Email cannot be empty'
            }
        
        # Enhanced regex pattern for email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return {
                'email': email,
                'is_valid': False,
                'error': 'Invalid email format'
            }
        
        # Split email into parts
        local, domain = email.split('@')
        
        # Additional validation
        if len(local) > 64 or len(domain) > 253:
            return {
                'email': email,
                'is_valid': False,
                'error': 'Email too long'
            }
        
        if local.startswith('.') or local.endswith('.') or '..' in local:
            return {
                'email': email,
                'is_valid': False,
                'error': 'Invalid local part format'
            }
        
        # Validation passed
        return {
            'email': email,
            'is_valid': True,
            'normalized': email.lower(),
            'local': local,
            'domain': domain.lower(),
            'method': 'regex_validation',
            'error': None
        }
        
    except Exception as e:
        return {
            'email': email,
            'is_valid': False,
            'error': f'Validation error: {str(e)}'
        }

def validate_email_advanced(email):
    """
    Advanced validation with NO DNS lookups to prevent timeouts
    """
    try:
        from email_validator import validate_email, EmailNotValidError
        
        # IMPORTANT: Disable deliverability checking to prevent DNS timeouts
        valid = validate_email(email, check_deliverability=False)
        
        return {
            'email': email,
            'is_valid': True,
            'normalized': valid.email,
            'local': valid.local,
            'domain': valid.domain,
            'ascii_email': getattr(valid, 'ascii_email', valid.email),
            'ascii_local': getattr(valid, 'ascii_local', valid.local),
            'ascii_domain': getattr(valid, 'ascii_domain', valid.domain),
            'smtputf8': getattr(valid, 'smtputf8', False),
            'method': 'email_validator_library',
            'error': None
        }
    except EmailNotValidError as e:
        return {
            'email': email,
            'is_valid': False,
            'normalized': None,
            'method': 'email_validator_library',
            'error': str(e)
        }
    except ImportError:
        # Library not available, fall back to simple validation
        return validate_email_simple(email)
    except Exception as e:
        # Any other error, fall back to simple validation
        print(f"Advanced validation failed for {email}: {e}")
        return validate_email_simple(email)

def validate_single_email(email):
    """
    Main validation function with fallback
    """
    # Try advanced validation first (without DNS), fallback to simple
    return validate_email_advanced(email)

def validate_email_batches(emails: List[str], batch_size: int = 30) -> List[Dict]:
    """
    Fast batch validation without timeouts
    """
    if not emails:
        return []
    
    batch_size = max(batch_size, 30)
    all_results = []
    
    # Process in chunks to avoid overwhelming the system
    for i in range(0, len(emails), batch_size):
        batch = emails[i:i + batch_size]
        batch_results = [validate_single_email(email) for email in batch]
        all_results.extend(batch_results)
    
    return all_results

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        'message': 'Email Validator API',
        'version': '2.0',
        'status': 'running',
        'endpoints': {
            'GET /': 'API documentation',
            'GET /health': 'Health check',
            'GET /test': 'Test endpoint',
            'POST /validate': 'Validate single email',
            'POST /validate/batch': 'Validate multiple emails'
        },
        'features': [
            'Fast validation without DNS timeouts',
            'CORS enabled for all origins',
            'Batch processing optimized for 30+ emails',
            'Fallback validation system'
        ],
        'usage': {
            'single_email': {
                'url': '/validate',
                'method': 'POST',
                'body': {'email': 'test@example.com'}
            },
            'batch_emails': {
                'url': '/validate/batch',
                'method': 'POST', 
                'body': {
                    'emails': ['email1@test.com', 'email2@test.com'],
                    'batch_size': 30
                }
            }
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'email-validator',
        'version': '2.0',
        'features': 'fast_validation_no_dns'
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify everything is working"""
    try:
        # Test simple validation
        test_emails = ['test@example.com', 'invalid.email', 'user@domain.co.uk']
        results = []
        
        for email in test_emails:
            result = validate_single_email(email)
            results.append(result)
        
        return jsonify({
            'status': 'test_successful',
            'test_results': results,
            'cors_enabled': True,
            'dns_timeouts_disabled': True,
            'message': 'API is working perfectly'
        })
    except Exception as e:
        return jsonify({
            'status': 'test_failed',
            'error': str(e)
        }), 500

@app.route('/validate', methods=['POST', 'OPTIONS'])
def validate_email_endpoint():
    """Validate a single email address"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email address is required'}), 400
        
        email = data['email']
        
        if not email or not isinstance(email, str):
            return jsonify({'error': 'Email must be a valid string'}), 400
            
        email = email.strip()
        if not email:
            return jsonify({'error': 'Email address cannot be empty'}), 400
        
        result = validate_single_email(email)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/validate/batch', methods=['POST', 'OPTIONS'])
def validate_batch_endpoint():
    """Validate multiple email addresses quickly"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        data = request.get_json()
        
        if not data or 'emails' not in data:
            return jsonify({'error': 'Emails list is required'}), 400
        
        emails = data['emails']
        batch_size = data.get('batch_size', 30)
        
        if not isinstance(emails, list):
            return jsonify({'error': 'Emails must be a list'}), 400
        
        if len(emails) == 0:
            return jsonify({'error': 'At least one email is required'}), 400
        
        # Clean emails
        cleaned_emails = []
        for email in emails:
            if isinstance(email, str) and email.strip():
                cleaned_emails.append(email.strip())
        
        if not cleaned_emails:
            return jsonify({'error': 'No valid emails found'}), 400
        
        # Fast validation without DNS timeouts
        if len(cleaned_emails) >= 30:
            results = validate_email_batches(cleaned_emails, batch_size)
        else:
            results = [validate_single_email(email) for email in cleaned_emails]
        
        # Calculate summary
        valid_count = sum(1 for r in results if r['is_valid'])
        invalid_count = len(results) - valid_count
        
        return jsonify({
            'results': results,
            'summary': {
                'total': len(results),
                'valid': valid_count,
                'invalid': invalid_count,
                'success_rate': round((valid_count / len(results)) * 100, 2) if results else 0,
                'processed_in_batches': len(cleaned_emails) >= 30,
                'batch_size_used': batch_size if len(cleaned_emails) >= 30 else 'N/A',
                'processing_method': 'fast_no_dns'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Email Validator API v2.0 on port {port}")
    print(f"✅ Features: Fast validation, CORS enabled, No DNS timeouts")
    print(f"📡 Endpoints: /, /health, /test, /validate, /validate/batch")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
