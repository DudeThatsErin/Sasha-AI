#!/usr/bin/env python3
"""
Script to train the initial Sasha AI model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.model_trainer import train_with_sample_data

if __name__ == "__main__":
    print("Training initial Sasha AI model...")
    train_with_sample_data()
    print("Initial training complete!")
