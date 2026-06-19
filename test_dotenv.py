#!/usr/bin/env python3
"""Test dotenv loading with symlinked .env file"""

import os
from dotenv import load_dotenv

print("=" * 60)
print("Testing dotenv with symlinked .env")
print("=" * 60)

# Get current directory
cwd = os.getcwd()
print(f"\nCurrent directory: {cwd}")

# Check if .env exists
env_path = ".env"
print(f"Looking for .env at: {os.path.abspath(env_path)}")
print(f"File exists: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    # Check if it's a symlink
    is_symlink = os.path.islink(env_path)
    print(f"Is symlink: {is_symlink}")
    if is_symlink:
        link_target = os.readlink(env_path)
        print(f"Links to: {link_target}")

# Test 1: Default load_dotenv()
print("\n" + "-" * 60)
print("Test 1: load_dotenv() - default behavior")
print("-" * 60)

# Clear env first
if "ISSUER" in os.environ:
    del os.environ["ISSUER"]

load_dotenv()
issuer = os.getenv("ISSUER")
print(f"ISSUER after load_dotenv(): {issuer}")

# Test 2: Explicit path
print("\n" + "-" * 60)
print("Test 2: load_dotenv(filepath) - explicit path")
print("-" * 60)

# Clear env first
if "ISSUER" in os.environ:
    del os.environ["ISSUER"]

filepath = os.path.join(os.path.dirname(__file__), ".env")
print(f"Loading from: {filepath}")
load_dotenv(filepath)
issuer = os.getenv("ISSUER")
print(f"ISSUER after load_dotenv(filepath): {issuer}")

# Test 3: Absolute path
print("\n" + "-" * 60)
print("Test 3: load_dotenv(absolute_path)")
print("-" * 60)

# Clear env first
if "ISSUER" in os.environ:
    del os.environ["ISSUER"]

abs_path = os.path.abspath(".env")
print(f"Loading from: {abs_path}")
load_dotenv(abs_path)
issuer = os.getenv("ISSUER")
print(f"ISSUER after load_dotenv(absolute_path): {issuer}")

print("\n" + "=" * 60)
print("All .env entries loaded:")
print("=" * 60)
for key in ["AWS_ACCOUNT_ID", "MAHESH_AWS_ROLE", "AWS_USER_ID", "AWS_DEFAULT_REGION", "ISSUER"]:
    val = os.getenv(key)
    print(f"{key}: {val}")

print("\n" + "=" * 60)
