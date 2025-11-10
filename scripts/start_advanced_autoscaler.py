#!/usr/bin/env python3
"""
Start Advanced Auto-Scaler (Phase 3)
Enhanced auto-scaling with scheduled policies, multi-metric decisions, and analytics
"""

import sys
import os

# Add the scripts directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_autoscaler import AdvancedAutoScaler

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 STARTING ADVANCED AUTO-SCALER (Phase 3)")
    print("=" * 60)
    print("Features:")
    print("  ✅ Schedule-based scaling")
    print("  ✅ Multi-metric scaling decisions") 
    print("  ✅ Advanced cooldown and rate limiting")
    print("  ✅ Scaling history analytics")
    print("  ✅ Container health monitoring")
    print("=" * 60)
    
    try:
        scaler = AdvancedAutoScaler()
        scaler.start()
    except KeyboardInterrupt:
        print("\n🛑 Advanced Auto-Scaler stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting Advanced Auto-Scaler: {e}")
        sys.exit(1)