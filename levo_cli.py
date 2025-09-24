#!/usr/bin/env python3
"""
Levo CLI Entry Point
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.levo import cli

if __name__ == '__main__':
    cli()
