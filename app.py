#!/usr/bin/env python3
"""
Web API Email Validator using Flask
FIXED VERSION with CORS headers
"""

from flask import Flask, request, jsonify
from flask_cors import CORS  # ADD THIS LINE
from email_validator import validate_email, EmailNotValidError
import os
from typing import List, Dict

app = Flask(__name__)
CORS(app)  # ADD THIS LINE - Enables CORS for all routes

def validate_single_email(email):
    """
    Validate a single email address
    """
    try:
        valid = validate_email(email)
        return {
            'email': email,
            'is_valid': True,
            'normalized': valid.email,
            'local': valid.local,
            'domain': valid.domain,
            'ascii_email': valid.ascii_email,
            'ascii_local': valid.ascii_local,
            'ascii_domain': valid.ascii_domain,
            'smtputf8': valid.smtputf8,
            'error': None
        }
    except EmailNotValidError as e:
        return {
            'email': email,
            'is_valid': False,
            'normalized': None,
            'error': str(e)
        }

def chunk_emails(emails: List[str], batch_size: int = 30):
    """Split email list into chunks"""
    batch_size = max(batch_size, 30)
    for i in range(0, len(emails), batch_size):
        yield emails[i:i + batch_size]

def validate_email_batches(emails: List[str], batch_size: int = 30) -> List[Dict]:
    """Validate emails in batches"""
    if not emails:
        return []
    
    batch_size = max(batch_size, 30)
    all_results = []
    
    for batch in chunk_emails(emails, batch_size):
        batch_results = [validate_single_email(email) for email in batch]
        all_results.extend(batch_results)
    
    return all_results

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        'message': 'Email Validator API',
        'version': '1.0',
        'endpoints': {
            'POST /validate': 'Validate single email',
            'POST /validate/batch': 'Validate multiple emails (minimum 30 for batch processing)',
            'GET /health': 'Health check'
        },
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
    return jsonify({'status': 'healthy', 'service': 'email-validator'})

@app.route('/validate', methods=['POST'])
def validate_email_endpoint():
    """Validate a single email address"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email address is required'}), 400
        
        email = data['email'].strip()
        if not email:
            return jsonify({'error': 'Email address cannot be empty'}), 400
        
        result = validate_single_email(email)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/validate/batch', methods=['POST'])
def validate_batch_endpoint():
    """Validate multiple email addresses"""
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
        emails = [email.strip() for email in emails if email.strip()]
        
        if len(emails) >= 30:
            results = validate_email_batches(emails, batch_size)
        else:
            # For smaller batches, use regular processing
            results = [validate_single_email(email) for email in emails]
        
        # Summary statistics
        valid_count = sum(1 for r in results if r['is_valid'])
        invalid_count = len(results) - valid_count
        
        return jsonify({
            'results': results,
            'summary': {
                'total': len(results),
                'valid': valid_count,
                'invalid': invalid_count,
                'success_rate': round((valid_count / len(results)) * 100, 2) if results else 0,
                'processed_in_batches': len(emails) >= 30,
                'batch_size_used': batch_size if len(emails) >= 30 else 'N/A'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
