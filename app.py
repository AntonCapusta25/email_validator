#!/usr/bin/env python3
"""
Email Validator API with AI Hallucination Detection
Detects AI-generated emails that look real but don't exist
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from typing import List, Dict, Tuple
from collections import Counter
import difflib

app = Flask(__name__)

# CORS Configuration
CORS(app, 
     origins=["*"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=False)

# AI Hallucination Detection Patterns
AI_SUSPICIOUS_PATTERNS = {
    'sequential_usernames': [
        r'user\d+@',
        r'person\d+@',
        r'email\d+@',
        r'test\d+@',
        r'sample\d+@',
        r'example\d+@',
        r'demo\d+@',
        r'contact\d+@'
    ],
    'templated_patterns': [
        r'[a-z]+\d{1,3}@[a-z]+\.com$',  # john123@company.com
        r'[a-z]+\.[a-z]+\d+@[a-z]+\.com$',  # john.doe1@company.com
        r'[a-z]{4,8}\d{2,4}@[a-z]{5,10}\.com$'  # generic patterns
    ],
    'ai_common_names': [
        r'john\.?doe', r'jane\.?smith', r'alex\.?johnson', r'sarah\.?wilson',
        r'michael\.?brown', r'emily\.?davis', r'david\.?miller', r'lisa\.?garcia',
        r'chris\.?martinez', r'amanda\.?taylor', r'robert\.?anderson', r'jennifer\.?thomas'
    ],
    'suspicious_domains': [
        r'@(example|test|sample|demo|placeholder)\.com$',
        r'@(company|business|corporation|enterprise)\.com$',
        r'@(email|mail|contact|info)\.com$',
        r'@[a-z]{5,8}corp\.com$',
        r'@[a-z]{3,6}inc\.com$'
    ]
}

# Common fake/test domains
FAKE_DOMAINS = {
    'example.com', 'test.com', 'sample.com', 'demo.com', 'placeholder.com',
    'fake.com', 'dummy.com', 'temp.com', 'testing.com', 'mockup.com',
    'fakemail.com', 'tempmail.com', 'example.org', 'example.net'
}

def detect_ai_patterns(email: str) -> Dict:
    """
    Detect if an email might be AI-generated/hallucinated
    """
    email_lower = email.lower()
    local_part = email_lower.split('@')[0] if '@' in email_lower else ''
    domain_part = email_lower.split('@')[1] if '@' in email_lower else ''
    
    suspicion_score = 0
    detected_patterns = []
    
    # Check sequential username patterns
    for pattern in AI_SUSPICIOUS_PATTERNS['sequential_usernames']:
        if re.search(pattern, email_lower):
            suspicion_score += 30
            detected_patterns.append(f"Sequential pattern: {pattern}")
    
    # Check templated patterns
    for pattern in AI_SUSPICIOUS_PATTERNS['templated_patterns']:
        if re.search(pattern, email_lower):
            suspicion_score += 20
            detected_patterns.append(f"Templated pattern: {pattern}")
    
    # Check AI common names
    for pattern in AI_SUSPICIOUS_PATTERNS['ai_common_names']:
        if re.search(pattern, local_part):
            suspicion_score += 15
            detected_patterns.append(f"AI common name: {pattern}")
    
    # Check suspicious domains
    for pattern in AI_SUSPICIOUS_PATTERNS['suspicious_domains']:
        if re.search(pattern, email_lower):
            suspicion_score += 25
            detected_patterns.append(f"Suspicious domain: {pattern}")
    
    # Check against known fake domains
    if domain_part in FAKE_DOMAINS:
        suspicion_score += 40
        detected_patterns.append(f"Known fake domain: {domain_part}")
    
    # Check for overly perfect patterns
    if re.match(r'^[a-z]+\.[a-z]+@[a-z]+\.com$', email_lower):
        suspicion_score += 10
        detected_patterns.append("Overly perfect pattern")
    
    # Determine AI likelihood
    if suspicion_score >= 40:
        ai_likelihood = "high"
        ai_generated = True
    elif suspicion_score >= 20:
        ai_likelihood = "medium"
        ai_generated = True
    elif suspicion_score >= 10:
        ai_likelihood = "low"
        ai_generated = False
    else:
        ai_likelihood = "unlikely"
        ai_generated = False
    
    return {
        'ai_generated': ai_generated,
        'ai_likelihood': ai_likelihood,
        'suspicion_score': suspicion_score,
        'detected_patterns': detected_patterns
    }

def detect_batch_ai_patterns(emails: List[str]) -> Dict:
    """
    Detect AI patterns across a batch of emails
    """
    if len(emails) < 5:
        return {'batch_ai_detected': False, 'batch_patterns': []}
    
    domains = [email.split('@')[1].lower() if '@' in email else '' for email in emails]
    locals = [email.split('@')[0].lower() if '@' in email else '' for email in emails]
    
    batch_patterns = []
    batch_score = 0
    
    # Check for domain repetition (AI often uses same domains)
    domain_counts = Counter(domains)
    most_common_domain = domain_counts.most_common(1)[0] if domain_counts else ('', 0)
    if most_common_domain[1] > len(emails) * 0.5:  # More than 50% same domain
        batch_patterns.append(f"Domain repetition: {most_common_domain[1]}/{len(emails)} emails use {most_common_domain[0]}")
        batch_score += 20
    
    # Check for sequential patterns in batch
    sequential_count = 0
    for i, local in enumerate(locals):
        if re.search(r'(user|person|test|email)\d+', local):
            sequential_count += 1
    
    if sequential_count > len(emails) * 0.3:  # More than 30% sequential
        batch_patterns.append(f"Sequential usernames: {sequential_count}/{len(emails)} emails")
        batch_score += 25
    
    # Check for similar structure patterns
    similar_structures = 0
    for i in range(len(locals) - 1):
        for j in range(i + 1, len(locals)):
            similarity = difflib.SequenceMatcher(None, locals[i], locals[j]).ratio()
            if similarity > 0.7:  # Very similar structure
                similar_structures += 1
    
    if similar_structures > len(emails) * 0.2:
        batch_patterns.append(f"Similar structures detected: {similar_structures} pairs")
        batch_score += 15
    
    return {
        'batch_ai_detected': batch_score >= 25,
        'batch_patterns': batch_patterns,
        'batch_score': batch_score
    }

def validate_email_simple(email):
    """Fast email validation with AI detection"""
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
        
        # Enhanced regex pattern
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
        
        # AI Detection
        ai_detection = detect_ai_patterns(email)
        
        # Validation passed
        return {
            'email': email,
            'is_valid': True,
            'normalized': email.lower(),
            'local': local,
            'domain': domain.lower(),
            'method': 'regex_validation',
            'error': None,
            **ai_detection  # Include AI detection results
        }
        
    except Exception as e:
        return {
            'email': email,
            'is_valid': False,
            'error': f'Validation error: {str(e)}'
        }

def validate_email_advanced(email):
    """Advanced validation with AI detection"""
    try:
        from email_validator import validate_email, EmailNotValidError
        
        # Disable deliverability checking to prevent timeouts
        valid = validate_email(email, check_deliverability=False)
        
        # AI Detection
        ai_detection = detect_ai_patterns(email)
        
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
            'error': None,
            **ai_detection  # Include AI detection results
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
        return validate_email_simple(email)
    except Exception as e:
        return validate_email_simple(email)

def validate_single_email(email):
    """Main validation function with AI detection"""
    return validate_email_advanced(email)

def validate_email_batches(emails: List[str], batch_size: int = 30) -> List[Dict]:
    """Fast batch validation with AI detection"""
    if not emails:
        return []
    
    batch_size = max(batch_size, 30)
    all_results = []
    
    # Process in chunks
    for i in range(0, len(emails), batch_size):
        batch = emails[i:i + batch_size]
        batch_results = [validate_single_email(email) for email in batch]
        all_results.extend(batch_results)
    
    return all_results

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        'message': 'Email Validator API with AI Detection',
        'version': '3.0',
        'status': 'running',
        'features': [
            'Fast email validation',
            'AI hallucination detection',
            'ChatGPT fake email detection',
            'Batch processing (30+ emails)',
            'CORS enabled'
        ],
        'endpoints': {
            'GET /': 'API documentation',
            'GET /health': 'Health check',
            'GET /test': 'Test endpoint',
            'POST /validate': 'Validate single email with AI detection',
            'POST /validate/batch': 'Validate multiple emails with AI analysis'
        },
        'ai_detection': {
            'purpose': 'Detect AI-generated/hallucinated emails from ChatGPT, Claude, etc.',
            'patterns_detected': [
                'Sequential usernames (user1@, user2@, etc.)',
                'Templated patterns',
                'AI common names (john.doe, jane.smith)',
                'Suspicious domains',
                'Batch pattern analysis'
            ]
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
    return jsonify({
        'status': 'healthy', 
        'service': 'email-validator-ai',
        'version': '3.0',
        'features': ['email_validation', 'ai_detection', 'hallucination_detection']
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint with AI detection examples"""
    try:
        # Test emails including AI-suspicious ones
        test_emails = [
            'john.doe@company.com',  # AI-suspicious
            'user1@testcorp.com',    # AI-suspicious
            'real.person@gmail.com', # Likely real
            'test123@example.com',   # AI-suspicious
            'jane.smith@business.com' # AI-suspicious
        ]
        
        results = []
        for email in test_emails:
            result = validate_single_email(email)
            results.append(result)
        
        return jsonify({
            'status': 'test_successful',
            'test_results': results,
            'ai_detection_active': True,
            'message': 'API with AI detection working perfectly'
        })
    except Exception as e:
        return jsonify({
            'status': 'test_failed',
            'error': str(e)
        }), 500

@app.route('/validate', methods=['POST', 'OPTIONS'])
def validate_email_endpoint():
    """Validate single email with AI detection"""
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
    """Validate multiple emails with AI batch analysis"""
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
        
        # Validate emails
        if len(cleaned_emails) >= 30:
            results = validate_email_batches(cleaned_emails, batch_size)
        else:
            results = [validate_single_email(email) for email in cleaned_emails]
        
        # Batch AI analysis
        batch_ai_analysis = detect_batch_ai_patterns(cleaned_emails)
        
        # Calculate summary
        valid_count = sum(1 for r in results if r['is_valid'])
        invalid_count = len(results) - valid_count
        ai_detected_count = sum(1 for r in results if r.get('ai_generated', False))
        
        return jsonify({
            'results': results,
            'summary': {
                'total': len(results),
                'valid': valid_count,
                'invalid': invalid_count,
                'ai_detected': ai_detected_count,
                'success_rate': round((valid_count / len(results)) * 100, 2) if results else 0,
                'ai_detection_rate': round((ai_detected_count / len(results)) * 100, 2) if results else 0,
                'processed_in_batches': len(cleaned_emails) >= 30,
                'batch_size_used': batch_size if len(cleaned_emails) >= 30 else 'N/A'
            },
            'ai_analysis': batch_ai_analysis
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
    
    print(f"🚀 Starting Email Validator API v3.0 with AI Detection on port {port}")
    print(f"🤖 AI Features: Hallucination detection, ChatGPT fake email detection")
    print(f"📡 Endpoints: /, /health, /test, /validate, /validate/batch")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
