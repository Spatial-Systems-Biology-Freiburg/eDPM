# Run test suite
python -m pytest -v

# Build current project
python -m build

# Install twine if not already installed
python -m pip install twine

# Release the package
python -m twine upload dist/edpm-0.1.1*

