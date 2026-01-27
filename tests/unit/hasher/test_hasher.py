# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Test hasher"""

from graphrag_common.hasher import hash_data


def test_hash_data() -> None:
    """Test hash data function."""
    # Test different types of data

    class TestClass:  # noqa: B903
        """Test hasher class."""

        def __init__(self, value: str) -> None:
            self.value = value

    def _test_func():
        pass

    # All should work and not raise exceptions
    _ = hash_data("test string")
    _ = hash_data(12345)
    _ = hash_data(12.345)
    _ = hash_data([1, 2, 3, 4, 5])
    _ = hash_data({"key": "value", "number": 42})
    _ = hash_data((1, "two", 3.0))
    _ = hash_data({1, 2, 3, 4, 5})
    _ = hash_data(None)
    _ = hash_data(True)
    _ = hash_data(b"bytes data")
    _ = hash_data({"nested": {"list": [1, 2, 3], "dict": {"a": "b"}}})
    _ = hash_data(range(10))
    _ = hash_data(frozenset([1, 2, 3]))
    _ = hash_data(complex(1, 2))
    _ = hash_data(bytearray(b"byte array data"))
    _ = hash_data(memoryview(b"memory view data"))
    _ = hash_data(Exception("test exception"))
    _ = hash_data(TestClass)
    _ = hash_data(TestClass("instance value"))
    _ = hash_data(lambda x: x * 2)
    _ = hash_data(_test_func)

    # Test that equivalent data structures produce the same hash
    data1 = {
        "bool": True,
        "int": 42,
        "float": 3.14,
        "str": "hello, world",
        "list": [1, 2, 3],
        "dict": {"key": "value"},
        "nested": {
            "list_of_dicts": [{"a": 1}, {"b": 2}],
            "dict_of_lists": {"numbers": [1, 2, 3]},
        },
        "tuple": (1, 2, 3),
        "set": {1, 2, 3},
        "class": TestClass,
        "function": _test_func,
        "instance": TestClass("instance value"),
    }
    # Same data but different order
    data2 = {
        "bool": True,
        "list": [1, 2, 3],
        "float": 3.14,
        "str": "hello, world",
        "int": 42,
        "nested": {
            "dict_of_lists": {"numbers": [1, 2, 3]},
            "list_of_dicts": [{"a": 1}, {"b": 2}],
        },
        "dict": {"key": "value"},
        "tuple": (1, 2, 3),
        "class": TestClass,
        "set": {1, 3, 2},
        "instance": TestClass("instance value"),
        "function": _test_func,
    }

    hash1 = hash_data(data1)
    hash2 = hash_data(data2)

    assert hash1 == hash2, "Hashes should be the same for equivalent data structures"

    data3 = {"key1": "value1", "key2": 124, "key3": [1, 2, 3]}  # Different value
    hash3 = hash_data(data3)

    assert hash1 != hash3, "Hashes should be different for different data structures"

    # Test classes
    instance1 = TestClass("value1")
    instance2 = TestClass("value1")
    instance3 = TestClass("value2")
    hash_instance1 = hash_data(instance1)
    hash_instance2 = hash_data(instance2)
    hash_instance3 = hash_data(instance3)
    assert hash_instance1 == hash_instance2, (
        "Hashes should be the same for equivalent class instances"
    )
    assert hash_instance1 != hash_instance3, (
        "Hashes should be different for different class instances"
    )
