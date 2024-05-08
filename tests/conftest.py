# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
def pytest_addoption(parser):
    parser.addoption(
        "--run_slow", action="store_true", default=False, help="run slow tests"
    )
