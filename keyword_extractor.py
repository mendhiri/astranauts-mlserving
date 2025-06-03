import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re
import json

# Ensure necessary NLTK data is available (downloaded in a previous step)
# nltk.download('punkt')
# nltk.download('wordnet')
# nltk.download('stopwords')
# import json # Make sure json is imported at the top <- This line is removed

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def format_to_json(data_dict: dict, indent: int = 4) -> str:
    """
    Formats a Python dictionary into a JSON string.

    Args:
        data_dict: The dictionary to format.
        indent: The indentation level for pretty-printing the JSON.

    Returns:
        A JSON string representation of the dictionary, or an error message.
    """
    try:
        return json.dumps(data_dict, indent=indent, ensure_ascii=False)
    except TypeError as e:
        return f"Error formatting to JSON: {e}. Ensure all items in dict are JSON serializable."
    except Exception as e:
        return f"An unexpected error occurred during JSON formatting: {e}"

def preprocess_text(text: str) -> list[str]:
    """
    Tokenizes, lowercases, removes stop words, and lemmatizes text.

    Args:
        text: Raw text string.

    Returns:
        A list of processed (lemmatized) tokens.
    """
    if not text:
        return []
    tokens = word_tokenize(text.lower())
    processed_tokens = [
        lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in stop_words
    ]
    return processed_tokens

def extract_keywords_and_values(text: str, target_keywords: list[dict]) -> dict:
    """
    Extracts specified keywords and associated numerical values from text.

    Args:
        text: The input text string.
        target_keywords: A list of dictionaries, where each dictionary has
                         'keyword' (str, the canonical name) and
                         'variations' (list of str, synonyms/alternatives).

    Returns:
        A dictionary where keys are the canonical keywords and values are
        the first numerical value found after a keyword variation, or None.
    """
    extracted_data = {}
    if not text:
        return extracted_data

    # Preprocess the entire text once for keyword matching
    processed_text_tokens = preprocess_text(text)

    # For value extraction, we use the original text, tokenized and lowercased
    original_tokens_lower = [token.lower() for token in word_tokenize(text)]

    # Regex to find numbers (integer or decimal, possibly with commas)
    # It will also capture currency symbols if present, but the group(1) will be the number.
    # For simplicity, we'll extract the number part. A more complex regex could separate currency.
    # number_regex = r"[\$€£]?\s*(\d[\d,.]*\d)" # Original thought, but let's simplify for "next number"
    number_regex = r"(\d[\d,.]*\d)"


    for keyword_info in target_keywords:
        canonical_keyword = keyword_info['keyword']
        found_for_canonical = False # Flag to stop after first variation match for a canonical keyword

        # Lemmatize variations for matching against preprocessed text
        lemmatized_variations = [lemmatizer.lemmatize(var.lower()) for var in keyword_info['variations']]

        # Check if any lemmatized variation is in the preprocessed text
        matched_variation_in_processed = None
        for lm_var in lemmatized_variations:
            if lm_var in processed_text_tokens:
                matched_variation_in_processed = lm_var
                break

        if matched_variation_in_processed:
            # Keyword variation found. Now try to find its occurrence in original_tokens_lower
            # to get an index for searching the value. This is a bit naive as lemmatized
            # form might not map 1-to-1 to original token, but good for a start.
            # We'll search for original variations in original_tokens_lower.

            value_found = None
            start_search_index = 0

            # Iterate through original variations to find their first occurrence
            # and then look for a number after that.
            for original_variation in keyword_info['variations']:
                try:
                    # Find the first occurrence of the original variation (lowercase)
                    # in the original token list (lowercase)
                    current_pos = 0
                    while current_pos < len(original_tokens_lower):
                        try:
                            idx = original_tokens_lower.index(original_variation.lower(), current_pos)
                            # Search for a number in tokens following this keyword occurrence
                            for i in range(idx + 1, min(idx + 10, len(original_tokens_lower))): # Look in next 10 tokens
                                match = re.search(number_regex, original_tokens_lower[i])
                                if match:
                                    # Extract the number, remove commas to make it a clean float/int
                                    num_str = match.group(1).replace(',', '')
                                    # Basic check if it's a valid number
                                    if re.match(r"^\d+(\.\d+)?$", num_str):
                                        value_found = num_str
                                        found_for_canonical = True
                                        break
                                if value_found: break
                            current_pos = idx + 1 # Continue search for this variation if no value found yet
                            if found_for_canonical: break
                        except ValueError: # variation not found further
                            break
                    if found_for_canonical: break
                except ValueError:
                    # This specific original variation not in original_tokens_lower, try next
                    continue

            extracted_data[canonical_keyword] = value_found
            if found_for_canonical:
                continue # Move to the next canonical keyword

        # If no variation was found in processed text, still add key with None
        if canonical_keyword not in extracted_data:
             extracted_data[canonical_keyword] = None

    return extracted_data

# The first if __name__ == "__main__" block (identified above) is now deleted by this empty REPLACE block.
# The second, correct if __name__ == "__main__" block remains untouched below.

if __name__ == "__main__":
    target_keywords_list = [
        {'keyword': 'Income', 'variations': ['income', 'revenue', 'earnings', 'total income']},
        {'keyword': 'Expenses', 'variations': ['expenses', 'costs', 'expenditure']},
        {'keyword': 'Date', 'variations': ['date', 'period ending']}
    ]

    sample_text1 = "The company's total income for the year was $50,000. This revenue was higher than expected. Other earnings were $5,000."
    print(f"Text: \"{sample_text1}\"")
    extracted1 = extract_keywords_and_values(sample_text1, target_keywords_list)
    print(f"Extracted Data 1: {extracted1}")
    json_output1 = format_to_json(extracted1)
    print(f"JSON Output 1:\n{json_output1}\n")

    sample_text2 = "Report for Q2. Main revenue stream showed good performance. However, overall income is not specified numerically."
    print(f"\nText: \"{sample_text2}\"")
    extracted2 = extract_keywords_and_values(sample_text2, target_keywords_list)
    print(f"Extracted Data 2: {extracted2}")
    json_output2 = format_to_json(extracted2)
    print(f"JSON Output 2:\n{json_output2}\n")

    sample_text3 = "No financial data available for this period. Costs were high."
    print(f"\nText: \"{sample_text3}\"")
    extracted3 = extract_keywords_and_values(sample_text3, target_keywords_list)
    print(f"Extracted Data 3: {extracted3}")
    json_output3 = format_to_json(extracted3)
    print(f"JSON Output 3:\n{json_output3}\n")

    sample_text4 = "Yearly financial report. Total revenue: USD 1,234,567. Net earnings stood at 450K. Expenses this year are 300.000."
    print(f"\nText: \"{sample_text4}\"")
    extracted4 = extract_keywords_and_values(sample_text4, target_keywords_list)
    print(f"Extracted Data 4: {extracted4}")
    json_output4 = format_to_json(extracted4)
    print(f"JSON Output 4:\n{json_output4}\n")

    sample_text5 = "The date of this report is 2023-12-31. Income was 20000."
    print(f"\nText: \"{sample_text5}\"")
    extracted5 = extract_keywords_and_values(sample_text5, target_keywords_list)
    print(f"Extracted Data 5: {extracted5}")
    json_output5 = format_to_json(extracted5)
    print(f"JSON Output 5:\n{json_output5}\n")

    # Test for multi-token variation
    sample_text6 = "The company's total income for the year was $75,000."
    print(f"\nText: \"{sample_text6}\"")
    extracted6 = extract_keywords_and_values(sample_text6, [{'keyword': 'Total Income', 'variations': ['total income']}])
    # This will currently fail to find "total income" as a single unit in the preprocessed text
    # because preprocess_text splits "total income" into "total", "income".
    # And the matching logic for `original_variation.lower()` also expects single tokens.
    # This is a known limitation of the current simple approach.
    print(f"Extracted Data 6 (Test multi-token keyword): {extracted6}")
    json_output6 = format_to_json(extracted6)
    print(f"JSON Output 6 (Test multi-token keyword):\n{json_output6}\n")

    empty_text = ""
    print(f"\nText: \"{empty_text}\"")
    extracted_empty = extract_keywords_and_values(empty_text, target_keywords_list)
    print(f"Extracted Data (Empty Text): {extracted_empty}")
    json_output_empty = format_to_json(extracted_empty)
    print(f"JSON Output (Empty Text):\n{json_output_empty}\n")

    no_keywords_text = "Just some random words without any financial information."
    print(f"\nText: \"{no_keywords_text}\"")
    extracted_no_match = extract_keywords_and_values(no_keywords_text, target_keywords_list)
    print(f"Extracted Data (No Matching Keywords): {extracted_no_match}")
    json_output_no_match = format_to_json(extracted_no_match)
    print(f"JSON Output (No Matching Keywords):\n{json_output_no_match}\n")
