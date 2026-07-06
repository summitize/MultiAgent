@echo off
setlocal enabledelayedexpansion
cd /d "c:\Users\Sumeet.Boob\OneDrive - Brillio\GitHubRepo\MultiAgent\Consolidated_Portal"
python simple_test.py
timeout /t 2 /nobreak
type test_results.txt
