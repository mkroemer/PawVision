---
layout: page
title: Developer Guide
permalink: /development/
---
# General Development Information

## Setting Up Your Development Environment

 - **Clone the repository**:
	 ```bash
	 git clone https://github.com/mkroemer/PawVision.git
	 cd PawVision
	 ```
# 🧪 Running and Writing Tests

PawVision uses [pytest](https://docs.pytest.org/) for all unit and integration tests. All test files are located in the `tests/` directory and are organized by domain (e.g., config, statistics, web interface).

To run all tests:

```bash
python run_tests.py --all
```

To run a specific test file:

```bash
python run_tests.py --file tests/test_config.py
```

To run a specific test class:

```bash
python run_tests.py --class TestConfigManager
```

To run a specific test class in a file:

```bash
python run_tests.py --file tests/test_config.py --class TestConfigManager
```

- Place new tests in the appropriate domain file in `tests/`
- Use the `unittest` framework (pytest will auto-discover)
- Test files should be named `test_*.py`
- Use temporary files and directories for isolation
- Mock hardware and external dependencies for reliability

All tests should pass before submitting changes. Logging errors during test shutdown are harmless and only occur in test environments.
