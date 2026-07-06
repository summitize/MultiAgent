#!/usr/bin/env python
import subprocess
import os

os.chdir(r'c:\Users\Sumeet.Boob\OneDrive - Brillio\GitHubRepo\MultiAgent')

try:
    subprocess.run(['git', 'add', 'Consolidated_Portal/app.py'], check=True)
    print("✓ Files staged")
    
    subprocess.run(['git', 'commit', '-m', 'Fix: Export app as ASGI application explicitly for Gunicorn compatibility'], check=True)
    print("✓ Commit created")
    
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    print("✓ Code pushed successfully to GitHub!")
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
