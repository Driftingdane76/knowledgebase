import re
import datetime
import sys
import os

# Ensure project root is in path so we can import from qa_app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qa_app.redaction import redact_text_content, get_redacted_words_idx, is_valid_date

def run_redaction_test_suite():
    """
    Comprehensive test suite verifying CPR and Bank redaction across
    all real-world variations and edge cases discovered during image audit.
    """
    print("=" * 70)
    print("RUNNING CPR & BANK REDACTION TEST SUITE")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "Case 1 (pro_snippet_18): CPR next to competing word 'faktura'",
            "text": "Køb af ny skærm til hjemmearbejdspladsen. Cpr nummer på fakturaen er 211198-6941. Overfør venligst.",
            "must_redact": ["211198-6941"],
            "must_keep": ["Køb af ny skærm", "fakturaen"]
        },
        {
            "name": "Case 2 (pro_snippet_30): CPR with 'personnummer' label in chat sentence",
            "text": "Hej support. Mit personnummer er 241122-2984 og beløbet skulle være overført.",
            "must_redact": ["241122-2984"],
            "must_keep": ["Hej support", "personnummer"]
        },
        {
            "name": "Case 3 (pro_snippet_43 Row 1): Table Row CPR without 'CPR' on same line",
            "text": "AKTUELLE KUNDER\nKunde ID: #61244 | Henrik Pedersen | 280155-5436 | Aktiv",
            "must_redact": ["280155-5436"],
            "must_keep": ["#61244", "Henrik Pedersen", "Aktiv"]
        },
        {
            "name": "Case 4 (pro_snippet_43 Row 2 / snippet_2): 4-digit Reg + 10-digit Konto space format",
            "text": "Bankoplysninger: 1899 8593915315\nKonto: 9557 9418321921",
            "must_redact": ["1899 8593915315", "9557 9418321921"],
            "must_keep": ["Bankoplysninger"]
        },
        {
            "name": "Case 5: Standalone CPR in customer note (no keyword anywhere in text)",
            "text": "Notat fra opkald: Kunden hedder Christian og oplyser 150688-1122 til udbetaling.",
            "must_redact": ["150688-1122"],
            "must_keep": ["Notat fra opkald", "Christian"]
        },
        {
            "name": "Case 6: False-positive preservation - Order # and Phone numbers NOT redacted",
            "text": "Ordrenummer #84009 faktura ref FAK-99231 Tlf: +45 88 77 66 55",
            "must_redact": [],
            "must_keep": ["#84009", "FAK-99231", "+45 88 77 66 55"]
        }
    ]
    
    passed_count = 0
    failed_count = 0
    
    for idx, tc in enumerate(test_cases, 1):
        print(f"\n[{idx}] {tc['name']}")
        print(f"    Input:    \"{tc['text']}\"")
        result = redact_text_content(tc['text'])
        print(f"    Output:   \"{result}\"")
        
        tc_passed = True
        
        # Check that target PII is redacted
        for target in tc["must_redact"]:
            if target in result:
                print(f"    ❌ FAILED: '{target}' was NOT redacted!")
                tc_passed = False
            else:
                print(f"    ✓ Redacted '{target}' successfully.")
                
        # Check that safe words / IDs were preserved
        for safe in tc["must_keep"]:
            if safe not in result:
                print(f"    ❌ FAILED: Safe text '{safe}' was falsely removed!")
                tc_passed = False
                
        if tc_passed:
            passed_count += 1
            print(f"    >>> RESULT: PASSED")
        else:
            failed_count += 1
            print(f"    >>> RESULT: FAILED")
            
    print("\n" + "=" * 70)
    print(f"SUITE SUMMARY: {passed_count} Passed, {failed_count} Failed out of {len(test_cases)} cases")
    print("=" * 70)
    
    return failed_count == 0

if __name__ == '__main__':
    success = run_redaction_test_suite()
    if not success:
        sys.exit(1)
