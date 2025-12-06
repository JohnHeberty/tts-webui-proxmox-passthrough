"""
Text Quality Assurance Module

Pure functions for validating text quality before training.

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
"""
import re
from typing import List, Set, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class TextQualityReport:
    """Report of text quality analysis."""
    text: str
    is_valid: bool
    length: int
    oov_chars: Set[str]
    has_numbers: bool
    has_symbols: bool
    has_multiple_sentences: bool
    warnings: List[str]
    errors: List[str]
    
    def __str__(self):
        status = "✅ VALID" if self.is_valid else "❌ INVALID"
        return (
            f"TextQualityReport({status}, {self.length} chars, "
            f"{len(self.oov_chars)} OOV, {len(self.warnings)} warnings, "
            f"{len(self.errors)} errors)"
        )


def check_oov_chars(text: str, vocab: Set[str]) -> Set[str]:
    """
    Find characters in text that are not in vocabulary.
    
    Args:
        text: Text to check
        vocab: Set of allowed characters
        
    Returns:
        Set of out-of-vocabulary characters
        
    Example:
        >>> vocab = set('abcdefghijklmnopqrstuvwxyz ')
        >>> oov = check_oov_chars("Hello 123!", vocab)
        >>> print(oov)
        {'H', '1', '2', '3', '!'}
    """
    text_chars = set(text)
    return text_chars - vocab


def contains_numbers(text: str) -> bool:
    """
    Check if text contains numeric digits.
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains digits
        
    Example:
        >>> contains_numbers("Hello world")
        False
        >>> contains_numbers("Year 2025")
        True
    """
    return bool(re.search(r'\d', text))


def contains_symbols(text: str, allowed_symbols: str = ".,!?;:- '\"") -> bool:
    """
    Check if text contains symbols beyond allowed set.
    
    Args:
        text: Text to check
        allowed_symbols: String of allowed punctuation/symbols
        
    Returns:
        True if text contains disallowed symbols
        
    Example:
        >>> contains_symbols("Hello, world!")
        False
        >>> contains_symbols("Email: test@domain.com")
        True
    """
    allowed = set(allowed_symbols)
    text_symbols = set(c for c in text if not c.isalnum() and not c.isspace())
    return bool(text_symbols - allowed)


def count_sentences(text: str) -> int:
    """
    Count number of sentences in text.
    
    Simple heuristic: count sentence-ending punctuation.
    
    Args:
        text: Text to analyze
        
    Returns:
        Estimated number of sentences
        
    Example:
        >>> count_sentences("Hello. How are you? Fine!")
        3
    """
    # Count sentence-ending punctuation
    sentence_ends = re.findall(r'[.!?]+', text)
    return max(1, len(sentence_ends))


def check_text_quality(
    text: str,
    vocab: Set[str],
    min_length: int = 3,
    max_length: int = 200,
    allow_numbers: bool = False,
    allow_symbols: bool = True,
    allowed_symbols: str = ".,!?;:- '\"",
) -> TextQualityReport:
    """
    Comprehensive text quality check for training data.
    
    Args:
        text: Text to validate
        vocab: Set of allowed characters
        min_length: Minimum text length
        max_length: Maximum text length
        allow_numbers: Whether to allow numeric digits
        allow_symbols: Whether to allow symbols
        allowed_symbols: String of allowed punctuation (if allow_symbols=True)
        
    Returns:
        TextQualityReport with validation results
        
    Example:
        >>> vocab = set('abcdefghijklmnopqrstuvwxyz .,!?')
        >>> report = check_text_quality("Hello, world!", vocab)
        >>> print(report.is_valid)
        True
    """
    warnings = []
    errors = []
    
    # Check length
    length = len(text)
    if length < min_length:
        errors.append(f"Text too short ({length} < {min_length})")
    elif length > max_length:
        errors.append(f"Text too long ({length} > {max_length})")
    
    # Check for empty/whitespace only
    if not text.strip():
        errors.append("Text is empty or whitespace only")
    
    # Check OOV characters
    oov_chars = check_oov_chars(text, vocab)
    if oov_chars:
        errors.append(f"Out-of-vocabulary characters: {sorted(oov_chars)}")
    
    # Check numbers
    has_numbers = contains_numbers(text)
    if has_numbers and not allow_numbers:
        warnings.append("Text contains numbers (should be normalized)")
    
    # Check symbols
    has_symbols = contains_symbols(text, allowed_symbols)
    if has_symbols and not allow_symbols:
        warnings.append("Text contains special symbols (should be normalized)")
    
    # Check sentence count
    num_sentences = count_sentences(text)
    has_multiple = num_sentences > 1
    if num_sentences > 3:
        warnings.append(f"Text has {num_sentences} sentences (might be too complex)")
    
    # Determine validity
    is_valid = len(errors) == 0
    
    return TextQualityReport(
        text=text,
        is_valid=is_valid,
        length=length,
        oov_chars=oov_chars,
        has_numbers=has_numbers,
        has_symbols=has_symbols,
        has_multiple_sentences=has_multiple,
        warnings=warnings,
        errors=errors,
    )


def validate_text_for_training(
    text: str,
    vocab_file: str,
    normalize: bool = True,
    verbose: bool = False,
) -> tuple[bool, str, List[str]]:
    """
    Validate and optionally normalize text for F5-TTS training.
    
    This is a high-level function that combines vocabulary loading,
    optional normalization, and quality checking.
    
    Args:
        text: Text to validate
        vocab_file: Path to vocabulary file
        normalize: Whether to normalize text first (default: True)
        verbose: Print validation details (default: False)
        
    Returns:
        Tuple of (is_valid, processed_text, issues)
        
    Example:
        >>> valid, text, issues = validate_text_for_training(
        ...     "Year 2025 costs R$ 100",
        ...     "train/config/vocab.txt",
        ...     normalize=True
        ... )
        >>> print(f"Valid: {valid}, Issues: {len(issues)}")
    """
    from .vocab import load_vocab
    from .normalizer import normalize_text
    
    issues = []
    
    # Load vocabulary
    try:
        vocab = load_vocab(vocab_file)
    except Exception as e:
        return False, text, [f"Failed to load vocabulary: {e}"]
    
    # Normalize if requested
    processed_text = text
    if normalize:
        try:
            processed_text = normalize_text(text)
            if verbose and processed_text != text:
                print(f"Normalized: '{text}' -> '{processed_text}'")
        except Exception as e:
            issues.append(f"Normalization failed: {e}")
    
    # Convert vocab to set if needed
    vocab_set = set(vocab) if isinstance(vocab, list) else vocab
    
    # Quality check
    report = check_text_quality(
        processed_text,
        vocab_set,
        allow_numbers=False,  # Should be normalized
        allow_symbols=True,   # Punctuation is allowed
    )
    
    if verbose:
        print(report)
    
    # Collect issues
    issues.extend(report.warnings)
    issues.extend(report.errors)
    
    return report.is_valid, processed_text, issues


def get_text_stats(texts: List[str]) -> Dict[str, Any]:
    """
    Calculate statistics for a collection of texts.
    
    Args:
        texts: List of text strings
        
    Returns:
        Dictionary with statistics
        
    Example:
        >>> texts = ["Hello", "Hello world", "Hello world!"]
        >>> stats = get_text_stats(texts)
        >>> print(f"Average length: {stats['avg_length']:.1f}")
    """
    if not texts:
        return {
            'count': 0,
            'total_chars': 0,
            'avg_length': 0.0,
            'min_length': 0,
            'max_length': 0,
            'total_words': 0,
            'avg_words': 0.0,
        }
    
    lengths = [len(t) for t in texts]
    word_counts = [len(t.split()) for t in texts]
    
    return {
        'count': len(texts),
        'total_chars': sum(lengths),
        'avg_length': sum(lengths) / len(lengths),
        'min_length': min(lengths),
        'max_length': max(lengths),
        'total_words': sum(word_counts),
        'avg_words': sum(word_counts) / len(word_counts),
    }


# CLI for testing
if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Text quality assurance utility")
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check text quality')
    check_parser.add_argument('text', help='Text to check')
    check_parser.add_argument('--vocab', required=True, help='Vocabulary file')
    check_parser.add_argument('--normalize', action='store_true',
                             help='Normalize text before checking')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Check multiple texts from file')
    batch_parser.add_argument('input_file', help='File with one text per line')
    batch_parser.add_argument('--vocab', required=True, help='Vocabulary file')
    batch_parser.add_argument('--normalize', action='store_true',
                             help='Normalize texts before checking')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        valid, processed, issues = validate_text_for_training(
            args.text,
            args.vocab,
            normalize=args.normalize,
            verbose=True
        )
        
        if valid:
            print(f"\n✅ Text is valid")
            print(f"Processed: {processed}")
        else:
            print(f"\n❌ Text is invalid")
            print(f"Issues:")
            for issue in issues:
                print(f"  - {issue}")
        
        sys.exit(0 if valid else 1)
    
    elif args.command == 'batch':
        input_file = Path(args.input_file)
        if not input_file.exists():
            print(f"Error: File not found: {input_file}")
            sys.exit(1)
        
        texts = input_file.read_text(encoding='utf-8').strip().split('\n')
        
        print(f"Checking {len(texts)} texts...")
        print()
        
        valid_count = 0
        invalid_count = 0
        all_issues = []
        
        for i, text in enumerate(texts, 1):
            valid, processed, issues = validate_text_for_training(
                text,
                args.vocab,
                normalize=args.normalize,
                verbose=False
            )
            
            if valid:
                valid_count += 1
                print(f"{i}. ✅ {text[:50]}...")
            else:
                invalid_count += 1
                print(f"{i}. ❌ {text[:50]}...")
                for issue in issues:
                    print(f"      - {issue}")
                all_issues.extend(issues)
        
        print()
        print(f"Results:")
        print(f"  Valid: {valid_count}")
        print(f"  Invalid: {invalid_count}")
        print(f"  Total issues: {len(all_issues)}")
        
        # Show stats
        stats = get_text_stats(texts)
        print()
        print(f"Statistics:")
        print(f"  Average length: {stats['avg_length']:.1f} chars")
        print(f"  Min/Max: {stats['min_length']}/{stats['max_length']} chars")
        print(f"  Average words: {stats['avg_words']:.1f}")
    
    else:
        parser.print_help()
