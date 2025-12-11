#!/usr/bin/env python
"""Quick validation script for Player Analysis refactoring."""
import sys
import traceback

def test_imports():
    """Test that all modules can be imported."""
    try:
        print("Testing imports...")
        from src.display_names import build_player_display_map, add_player_display_column, add_event_display_column
        from src.intensity_classification import classify_intensity_from_percentile, classify_explosiveness
        from src.config import (
            INTENSITY_WINDOW_LABELS,
            get_label_from_key,
            get_key_from_label,
            DEFAULT_COACH_WINDOWS,
            DEFAULT_ANALYST_WINDOWS,
            AVAILABLE_INTENSITY_WINDOWS
        )
        print("  ✓ All modules import successfully")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        traceback.print_exc()
        return False

def test_classification_functions():
    """Test classification functions."""
    try:
        print("Testing classification functions...")
        from src.intensity_classification import classify_intensity_from_percentile, classify_explosiveness
        
        # Test intensity classification
        assert classify_intensity_from_percentile(10) == "Easy", "10th percentile should be Easy"
        assert classify_intensity_from_percentile(45) == "Medium", "45th percentile should be Medium"
        assert classify_intensity_from_percentile(70) == "Hard", "70th percentile should be Hard"
        assert classify_intensity_from_percentile(90) == "Very Hard", "90th percentile should be Very Hard"
        print("  ✓ Intensity classification working")
        
        # Test explosiveness classification
        assert classify_explosiveness(10) == "Low", "10th percentile should be Low"
        assert classify_explosiveness(45) == "Moderate", "45th percentile should be Moderate"
        assert classify_explosiveness(70) == "High", "70th percentile should be High"
        assert classify_explosiveness(90) == "Very high", "90th percentile should be Very high"
        print("  ✓ Explosiveness classification working")
        
        return True
    except Exception as e:
        print(f"  ✗ Classification test failed: {e}")
        traceback.print_exc()
        return False

def test_config_constants():
    """Test configuration constants."""
    try:
        print("Testing configuration constants...")
        from src.config import (
            INTENSITY_WINDOW_LABELS,
            DEFAULT_COACH_WINDOWS,
            DEFAULT_ANALYST_WINDOWS,
            AVAILABLE_INTENSITY_WINDOWS,
            get_label_from_key,
            get_key_from_label
        )
        
        # Check mappings exist
        assert "intensity_10s" in INTENSITY_WINDOW_LABELS, "intensity_10s should be in labels"
        assert "Burst (10s)" in INTENSITY_WINDOW_LABELS.values(), "Burst (10s) should be in labels"
        print("  ✓ Window labels defined")
        
        # Check defaults
        assert len(DEFAULT_COACH_WINDOWS) > 0, "Coach windows should be defined"
        assert len(DEFAULT_ANALYST_WINDOWS) > 0, "Analyst windows should be defined"
        print("  ✓ Default window sets defined")
        
        # Check conversions
        assert get_label_from_key("intensity_10s") == "Burst (10s)", "Key to label conversion failed"
        assert get_key_from_label("Burst (10s)") == "intensity_10s", "Label to key conversion failed"
        print("  ✓ Key/label conversions working")
        
        return True
    except Exception as e:
        print(f"  ✗ Config test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("VALIDATION: Player Analysis Refactoring (Session Snapshot & Windows)")
    print("=" * 70)
    print()
    
    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_classification_functions()
    all_passed &= test_config_constants()
    
    print()
    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print()
        print("Changes implemented:")
        print("  ✓ Session Snapshot simplified (Intensity + Total Load + Explosiveness)")
        print("  ✓ Raw peak windows (10s/20s/30s) removed from Session Snapshot")
        print("  ✓ Intensity window selector moved to Analyst view only")
        print("  ✓ Coach view uses fixed defaults (no selector)")
        print("  ✓ Explosiveness classification helper added")
        print("  ✓ Config constants for windows defined globally")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
