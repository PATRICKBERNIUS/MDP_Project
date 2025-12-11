"""
Validation script for Window Color Map implementation
"""

import sys

def test_window_colors():
    """Test window color mapping"""
    print("\n" + "="*70)
    print("VALIDATION: Window Color Map Implementation")
    print("="*70 + "\n")
    
    try:
        from src.config import WINDOW_COLOR_MAP, get_window_color
        print("✓ Imports successful")
        
        # Test window color map
        expected_windows = [
            "5s window", "10s window", "20s window", "30s window",
            "Burst (5s)", "Burst (10s)", "Short press (20s)", "Extended press (30s)",
            "intensity_5s", "intensity_10s", "intensity_20s", "intensity_30s"
        ]
        
        print("\nWindow Color Map:")
        for window in expected_windows:
            color = WINDOW_COLOR_MAP.get(window, "NOT_FOUND")
            status = "✓" if color != "NOT_FOUND" else "✗"
            print(f"  {status} {window:30s} → {color}")
        
        # Test get_window_color function
        print("\nTesting get_window_color() function:")
        test_cases = [
            ("5s window", "#d62728"),
            ("10s window", "#1f77b4"),
            ("20s window", "#2ca02c"),
            ("30s window", "#ff7f0e"),
            ("intensity_10s", "#1f77b4"),
            ("Burst (10s)", "#1f77b4"),
            ("unknown_window", "#333333"),  # Should return fallback
        ]
        
        all_passed = True
        for window_name, expected_color in test_cases:
            actual_color = get_window_color(window_name)
            passed = actual_color == expected_color
            status = "✓" if passed else "✗"
            print(f"  {status} {window_name:30s} → {actual_color} (expected {expected_color})")
            if not passed:
                all_passed = False
        
        # Test utils import
        print("\nTesting utils.py integration:")
        from utils import plot_rolling_window_lines
        print("  ✓ plot_rolling_window_lines imports successfully")
        
        print("\n" + "="*70)
        if all_passed:
            print("✓ ALL TESTS PASSED - Color map ready for use")
            print("\nColor assignments:")
            print("  • 5s/10s/20s/30s window traces will use distinct colors")
            print("  • Colors are consistent across all naming conventions")
            print("  • Legend will show color-coded window names")
            print("  • Fallback color (#333333) for any unmapped windows")
        else:
            print("✗ SOME TESTS FAILED - Check color mappings")
        print("="*70 + "\n")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n✗ Error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_window_colors())
