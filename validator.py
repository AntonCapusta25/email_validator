#!/usr/bin/env python3
"""
Email Validator using email-validator library with batch processing
Install required library: pip install email-validator
"""

from email_validator import validate_email, EmailNotValidError
import sys
import time
from typing import List, Dict, Iterator
import csv
from pathlib import Path


def validate_single_email(email):
    """
    Validate a single email address
    
    Args:
        email (str): Email address to validate
        
    Returns:
        dict: Validation result with status and details
    """
    try:
        # Validate and get normalized result
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


def chunk_emails(emails: List[str], batch_size: int = 30) -> Iterator[List[str]]:
    """
    Split email list into chunks of specified size (minimum 30)
    
    Args:
        emails (List[str]): List of email addresses
        batch_size (int): Size of each batch (minimum 30)
        
    Yields:
        List[str]: Batch of email addresses
    """
    batch_size = max(batch_size, 30)  # Ensure minimum batch size of 30
    
    for i in range(0, len(emails), batch_size):
        yield emails[i:i + batch_size]


def validate_email_list(emails):
    """
    Validate a list of email addresses
    
    Args:
        emails (list): List of email addresses to validate
        
    Returns:
        list: List of validation results
    """
    results = []
    for email in emails:
        results.append(validate_single_email(email))
    return results


def validate_email_batches(emails: List[str], 
                          batch_size: int = 30, 
                          delay_between_batches: float = 0.1,
                          show_progress: bool = True) -> List[Dict]:
    """
    Validate emails in batches with progress tracking
    
    Args:
        emails (List[str]): List of email addresses to validate
        batch_size (int): Size of each batch (minimum 30)
        delay_between_batches (float): Delay in seconds between batches
        show_progress (bool): Whether to show progress updates
        
    Returns:
        List[Dict]: List of validation results
    """
    if not emails:
        return []
    
    batch_size = max(batch_size, 30)  # Ensure minimum batch size of 30
    total_emails = len(emails)
    all_results = []
    
    if show_progress:
        print(f"Processing {total_emails} emails in batches of {batch_size}")
        print("=" * 50)
    
    batch_count = 0
    for batch in chunk_emails(emails, batch_size):
        batch_count += 1
        batch_start_time = time.time()
        
        if show_progress:
            processed = len(all_results)
            remaining = total_emails - processed
            print(f"Batch {batch_count}: Processing {len(batch)} emails "
                  f"({processed + 1}-{processed + len(batch)} of {total_emails})")
        
        # Process current batch
        batch_results = validate_email_list(batch)
        all_results.extend(batch_results)
        
        batch_time = time.time() - batch_start_time
        
        if show_progress:
            valid_in_batch = sum(1 for r in batch_results if r['is_valid'])
            invalid_in_batch = len(batch_results) - valid_in_batch
            print(f"  ✓ Valid: {valid_in_batch}, ✗ Invalid: {invalid_in_batch} "
                  f"(took {batch_time:.2f}s)")
        
        # Add delay between batches (except for the last batch)
        if len(all_results) < total_emails and delay_between_batches > 0:
            time.sleep(delay_between_batches)
    
    if show_progress:
        total_valid = sum(1 for r in all_results if r['is_valid'])
        total_invalid = len(all_results) - total_valid
        print("=" * 50)
        print(f"✅ Completed! Valid: {total_valid}, Invalid: {total_invalid}")
    
    return all_results


def process_email_file(file_path: str, 
                      email_column: str = 'email',
                      batch_size: int = 30,
                      output_file: str = None,
                      has_header: bool = True) -> List[Dict]:
    """
    Process emails from a CSV file in batches
    
    Args:
        file_path (str): Path to CSV file containing emails
        email_column (str): Name of the column containing email addresses
        batch_size (int): Size of each batch (minimum 30)
        output_file (str): Optional path to save results as CSV
        has_header (bool): Whether CSV file has header row
        
    Returns:
        List[Dict]: List of validation results
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    emails = []
    
    print(f"Reading emails from: {file_path}")
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            if has_header:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if email_column in row and row[email_column].strip():
                        emails.append(row[email_column].strip())
            else:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row and len(row) > 0 and row[0].strip():
                        emails.append(row[0].strip())
                        
    except Exception as e:
        raise Exception(f"Error reading file: {e}")
    
    if not emails:
        print("No emails found in file!")
        return []
    
    print(f"Found {len(emails)} emails to validate")
    
    # Process emails in batches
    results = validate_email_batches(emails, batch_size=batch_size)
    
    # Save results if output file specified
    if output_file:
        save_results_to_csv(results, output_file)
        print(f"Results saved to: {output_file}")
    
    return results


def save_results_to_csv(results: List[Dict], output_file: str):
    """
    Save validation results to CSV file
    
    Args:
        results (List[Dict]): Validation results
        output_file (str): Path to output CSV file
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        if not results:
            return
            
        fieldnames = ['email', 'is_valid', 'normalized', 'local', 'domain', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            # Only write relevant fields
            row = {
                'email': result['email'],
                'is_valid': result['is_valid'],
                'normalized': result.get('normalized', ''),
                'local': result.get('local', ''),
                'domain': result.get('domain', ''),
                'error': result.get('error', '')
            }
            writer.writerow(row)


def validate_email_with_options(email, check_deliverability=True):
    """
    Validate email with additional options
    
    Args:
        email (str): Email address to validate
        check_deliverability (bool): Whether to check if domain accepts email
        
    Returns:
        dict: Validation result
    """
    try:
        valid = validate_email(
            email,
            check_deliverability=check_deliverability
        )
        return {
            'email': email,
            'is_valid': True,
            'normalized': valid.email,
            'local': valid.local,
            'domain': valid.domain,
            'error': None
        }
    except EmailNotValidError as e:
        return {
            'email': email,
            'is_valid': False,
            'error': str(e)
        }


def interactive_validator():
    """
    Interactive email validator with batch processing options
    """
    print("=== Email Validator with Batch Processing ===")
    print("Options:")
    print("1. 'single' - Validate one email")
    print("2. 'batch' - Enter multiple emails manually")
    print("3. 'file' - Process emails from CSV file")
    print("4. 'large-batch' - Enter many emails with batch processing")
    print("5. 'quit' - Exit")
    
    while True:
        choice = input("\nMode (single/batch/file/large-batch/quit): ").lower().strip()
        
        if choice == 'quit':
            print("Goodbye!")
            break
            
        elif choice == 'single':
            email = input("Enter email address: ").strip()
            if email:
                result = validate_single_email(email)
                print_validation_result(result)
                
        elif choice == 'batch':
            print("Enter email addresses (one per line, empty line to finish):")
            emails = []
            while True:
                email = input().strip()
                if not email:
                    break
                emails.append(email)
            
            if emails:
                results = validate_email_list(emails)
                print_batch_results(results)
                
        elif choice == 'large-batch':
            print("Enter email addresses (one per line, empty line to finish):")
            emails = []
            while True:
                email = input().strip()
                if not email:
                    break
                emails.append(email)
            
            if emails:
                if len(emails) >= 30:
                    batch_size = int(input(f"Batch size (minimum 30, default 30): ") or 30)
                    delay = float(input("Delay between batches in seconds (default 0.1): ") or 0.1)
                    results = validate_email_batches(emails, batch_size=batch_size, delay_between_batches=delay)
                else:
                    print(f"Only {len(emails)} emails entered. Using regular batch processing.")
                    results = validate_email_list(emails)
                print_batch_results(results)
                
        elif choice == 'file':
            file_path = input("Enter CSV file path: ").strip()
            if file_path:
                try:
                    email_column = input("Email column name (default 'email'): ").strip() or 'email'
                    batch_size = int(input("Batch size (minimum 30, default 50): ") or 50)
                    output_file = input("Output file path (optional): ").strip() or None
                    has_header = input("File has header row? (y/n, default y): ").lower().strip() != 'n'
                    
                    results = process_email_file(
                        file_path, 
                        email_column=email_column,
                        batch_size=batch_size,
                        output_file=output_file,
                        has_header=has_header
                    )
                    print_batch_results(results)
                    
                except Exception as e:
                    print(f"Error processing file: {e}")
        else:
            print("Invalid choice. Please enter 'single', 'batch', 'file', 'large-batch', or 'quit'")


def batch_mode_cli(emails: List[str], batch_size: int = 30, output_file: str = None):
    """
    Command line batch processing mode
    
    Args:
        emails (List[str]): List of email addresses
        batch_size (int): Batch size (minimum 30)
        output_file (str): Optional output file path
    """
    print(f"Processing {len(emails)} emails in batch mode...")
    
    if len(emails) < 30:
        print("Warning: Less than 30 emails provided. Using regular processing.")
        results = validate_email_list(emails)
    else:
        results = validate_email_batches(emails, batch_size=batch_size)
    
    print_batch_results(results)
    
    if output_file:
        save_results_to_csv(results, output_file)
        print(f"Results saved to: {output_file}")
    
    return results


def print_validation_result(result):
    """
    Print formatted validation result for a single email
    """
    print(f"\n--- Validation Result ---")
    print(f"Email: {result['email']}")
    print(f"Valid: {result['is_valid']}")
    
    if result['is_valid']:
        print(f"Normalized: {result['normalized']}")
        print(f"Local part: {result['local']}")
        print(f"Domain: {result['domain']}")
        if 'ascii_email' in result:
            print(f"ASCII email: {result['ascii_email']}")
            print(f"Requires UTF8: {result['smtputf8']}")
    else:
        print(f"Error: {result['error']}")


def print_batch_results(results):
    """
    Print formatted validation results for multiple emails
    """
    print(f"\n--- Batch Validation Results ---")
    valid_count = sum(1 for r in results if r['is_valid'])
    invalid_count = len(results) - valid_count
    
    print(f"Total emails: {len(results)}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {invalid_count}")
    
    print("\n--- Valid Emails ---")
    for result in results:
        if result['is_valid']:
            print(f"✓ {result['email']} → {result['normalized']}")
    
    print("\n--- Invalid Emails ---")
    for result in results:
        if not result['is_valid']:
            print(f"✗ {result['email']} - {result['error']}")


def demo():
    """
    Demonstration of the email validator with batch processing
    """
    print("=== Email Validator Demo with Batch Processing ===\n")
    
    # Test emails - expanded list for batch demo
    test_emails = [
        "user@example.com",
        "user.name+tag@example.com", 
        "invalid.email",
        "test@test",
        "user@domain.co.uk",
        "user@sub.domain.com",
        "invalid@",
        "@invalid.com",
        "spaces in@email.com",
        "unicode.test@münchen.de",
        "test1@gmail.com",
        "test2@yahoo.com",
        "test3@hotmail.com",
        "test4@outlook.com",
        "test5@company.org",
        "test6@university.edu",
        "test7@government.gov",
        "test8@nonprofit.net",
        "test9@business.biz",
        "test10@personal.info",
        "test11@tech.io",
        "test12@startup.co",
        "test13@enterprise.com",
        "test14@global.international",
        "test15@local.dev",
        "invalid16@",
        "17invalid@domain",
        "test18@valid-domain.com",
        "test19@another-valid.org",
        "test20@final-test.net",
        # Add more to reach 30+ for batch demo
        "batch1@example.com",
        "batch2@example.com", 
        "batch3@example.com",
        "batch4@example.com",
        "batch5@example.com"
    ]
    
    print(f"Testing {len(test_emails)} email addresses:")
    print("Regular processing:")
    start_time = time.time()
    results_regular = validate_email_list(test_emails[:10])  # First 10
    regular_time = time.time() - start_time
    print(f"Processed 10 emails in {regular_time:.2f} seconds")
    
    print("\n" + "="*50)
    print("Batch processing (30+ emails):")
    start_time = time.time()
    results_batch = validate_email_batches(test_emails, batch_size=15, delay_between_batches=0.05)
    batch_time = time.time() - start_time
    print(f"Total time: {batch_time:.2f} seconds")
    
    # Summary
    valid_count = sum(1 for r in results_batch if r['is_valid'])
    invalid_count = len(results_batch) - valid_count
    print(f"\nFinal Summary:")
    print(f"Total emails processed: {len(results_batch)}")
    print(f"Valid emails: {valid_count}")
    print(f"Invalid emails: {invalid_count}")
    print(f"Success rate: {(valid_count/len(results_batch)*100):.1f}%")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            demo()
        elif sys.argv[1] == "interactive":
            interactive_validator()
        elif sys.argv[1] == "file":
            if len(sys.argv) < 3:
                print("Usage: python email_validator.py file <file_path> [batch_size] [output_file]")
                sys.exit(1)
            
            file_path = sys.argv[2]
            batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            output_file = sys.argv[4] if len(sys.argv) > 4 else None
            
            try:
                results = process_email_file(file_path, batch_size=batch_size, output_file=output_file)
                print(f"\nProcessed {len(results)} emails from file")
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)
                
        elif sys.argv[1] == "batch":
            if len(sys.argv) < 3:
                print("Usage: python email_validator.py batch <email1> <email2> ... [--batch-size=N] [--output=file.csv]")
                sys.exit(1)
            
            emails = []
            batch_size = 30
            output_file = None
            
            for arg in sys.argv[2:]:
                if arg.startswith("--batch-size="):
                    batch_size = int(arg.split("=")[1])
                elif arg.startswith("--output="):
                    output_file = arg.split("=")[1]
                else:
                    emails.append(arg)
            
            if emails:
                batch_mode_cli(emails, batch_size=batch_size, output_file=output_file)
            else:
                print("No emails provided!")
                
        else:
            # Validate emails passed as command line arguments
            emails = sys.argv[1:]
            if len(emails) >= 30:
                print("Large batch detected, using batch processing...")
                results = validate_email_batches(emails)
            else:
                results = validate_email_list(emails)
            print_batch_results(results)
    else:
        # Default: run interactive mode
        interactive_validator()
