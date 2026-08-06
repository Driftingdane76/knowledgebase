import os
import sys
import re

# Ensure project root is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from qa_app.redaction import redact_text_content, get_redacted_words_idx

def run_bank_precision_tests():
    print("=" * 75)
    print("RUNNING BANK REDACTION PRECISION & FALSE POSITIVE GUARD SUITE")
    print("=" * 75)
    
    test_cases = [
        # --- TRUE POSITIVES (MUST BE REDACTED) ---
        {
            "id": "TP1_LineWrappedBank",
            "name": "Line-wrapped bank account under Reg/Konto label",
            "input": "NemKonto / Betaling: Reg.nr: 8496 - Kontonr:\n4091376335",
            "must_contain": ["[REDACTED", "4091376335" not in "output"], # Account number must be redacted
            "target_unmasked": "4091376335"
        },
        {
            "id": "TP2_SeparateKontoKeyword",
            "name": "Konto on its own line before number",
            "input": "Udbetaling til NemKonto:\n9384 1029384756",
            "must_contain": ["[REDACTED"],
            "target_unmasked": "1029384756"
        },
        {
            "id": "TP3_IBANDk",
            "name": "Danish IBAN formatted NemKonto",
            "input": "NemKonto: DK80 3437 8724 349941 bekræftet",
            "must_contain": ["[REDACTED"],
            "target_unmasked": "8724 349941"
        },

        # --- FALSE POSITIVES (MUST NEVER BE REDACTED) ---
        {
            "id": "FP1_CVR_CompanyID",
            "name": "Danish CVR company registration number",
            "input": "Selskabet Forsikring A/S CVR-nr: 12345678. Kontakt kundeservice.",
            "must_preserve": "12345678"
        },
        {
            "id": "FP2_CaseNumber",
            "name": "Case ID / Sagsnummer with 6-8 digits",
            "input": "Behandler henvendelse vedrørende Sag #00849201 og Kunde ID #KND-436825.",
            "must_preserve": "00849201"
        },
        {
            "id": "FP3_PolicyNumber",
            "name": "Insurance policy number",
            "input": "Tilknyttet police POL-IND-35886 samt police SF-889104 for kunden.",
            "must_preserve": "35886"
        },
        {
            "id": "FP4_DanishCurrency",
            "name": "Danish currency amounts with thousands separators",
            "input": "Forsikringssum er opgjort til 850.000 DKK og årlig præmie er 2.480 DKK.",
            "must_preserve": "850.000"
        },
        {
            "id": "FP5_PhoneAndPostal",
            "name": "Danish phone number and postal code",
            "input": "Adresse: Vesterbrogade 30, 1620 København V. Tlf: 33112233.",
            "must_preserve": "33112233"
        }
    ]
    
    passed = 0
    failed = 0
    
    for case in test_cases:
        output = redact_text_content(case["input"])
        print(f"\n[{case['id']}] {case['name']}")
        print(f"    Input:    {repr(case['input'])}")
        print(f"    Output:   {repr(output)}")
        
        case_passed = True
        
        # Check True Positive condition
        if "target_unmasked" in case:
            if case["target_unmasked"] in output:
                print(f"    ❌ FAILED: Sensitive bank number '{case['target_unmasked']}' was NOT redacted!")
                case_passed = False
            else:
                print(f"    ✓ Passed: Sensitive bank number properly redacted.")
                
        # Check False Positive guardrail condition
        if "must_preserve" in case:
            if case["must_preserve"] not in output:
                print(f"    ❌ FAILED: Non-sensitive value '{case['must_preserve']}' was falsely redacted!")
                case_passed = False
            else:
                print(f"    ✓ Passed: Non-sensitive value '{case['must_preserve']}' properly preserved.")
                
        if case_passed:
            passed += 1
        else:
            failed += 1
            
    print("\n" + "=" * 75)
    print(f"TEST SUITE RESULTS: {passed} Passed, {failed} Failed out of {len(test_cases)} cases")
    print("=" * 75)
    
    return failed == 0

if __name__ == '__main__':
    success = run_bank_precision_tests()
    if not success:
        sys.exit(1)
