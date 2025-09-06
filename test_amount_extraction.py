def test_amount_extraction():
    """Test the amount extraction logic"""
    
    # Test cases with different amount formats
    test_cases = [
        "₹50,000",
        "50000",
        "₹1,00,000",
        "100000",
        "₹25,500.50",
        "25500.50",
        "₹1,25,000.75",
        "125000.75"
    ]
    
    for amount_str in test_cases:
        try:
            # Remove any currency symbols, commas, etc.
            cleaned_amount = amount_str.replace('₹', '').replace(',', '').replace(' ', '')
            amount_value = float(cleaned_amount)
            print(f"Original: '{amount_str}' -> Extracted: {amount_value}")
        except ValueError as e:
            print(f"Error converting '{amount_str}': {e}")

if __name__ == "__main__":
    test_amount_extraction()
