#!/usr/bin/env python3
"""
Script to start automatic retraining monitor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.auto_retrainer import main

if __name__ == "__main__":
    print("Starting automatic retraining monitor...")
    main()
