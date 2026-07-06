import subprocess
import sys

result = subprocess.run(
    [sys.executable, "test_app.py"],
    cwd=r"c:\Users\Sumeet.Boob\OneDrive - Brillio\GitHubRepo\MultiAgent\Consolidated_Portal",
    capture_output=True,
    text=True,
    timeout=60
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print(f"Exit code: {result.returncode}")
