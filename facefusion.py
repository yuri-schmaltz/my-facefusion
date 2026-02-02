#!/usr/bin/env python3
"""
Compatibility shim for legacy entrypoint.
Redirects to faceforge.py so existing scripts keep working.
"""
import runpy

if __name__ == "__main__":
    runpy.run_module("faceforge", run_name="__main__")
