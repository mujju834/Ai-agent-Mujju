# setup.py
from setuptools import setup, find_packages

setup(
    name="browseruse",
    version="0.1",
    packages=find_packages(),        # picks up browseruse/
    py_modules=[
      "ai_agent",
      "agent_functions",
      "browser_controller"
    ],  
)
