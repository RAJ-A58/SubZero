#!/usr/bin/env python3
"""
SubZero — Quick start script.
Adds server/ and sandbox/ to PYTHONPATH so imports resolve correctly,
then launches uvicorn.
"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(__file__))
env = os.environ.copy()
env["PYTHONPATH"] = os.pathsep.join([
    os.path.join(os.getcwd(), "server"),
    os.path.join(os.getcwd(), "sandbox"),
])
subprocess.run(
    [sys.executable, "-m", "uvicorn", "server.app:app", "--reload", "--port", "8000"],
    env=env,
)
