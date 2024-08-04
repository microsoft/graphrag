from graphrag.llm.openai.utils import try_parse_json_object


async def test_try_parse_json_object() -> None:
    test_cases = [
        {
            "description": "Valid JSON with markdown",
            "input": """```json
    {
        "points": [
            {"description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.", "score": 0}
        ]
    }
    ```""",
            "expected_output": """{
        "points": [
            {"description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.", "score": 0}
        ]
    }""",
            "expected_dict": {
                "points": [
                    {
                        "description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.",
                        "score": 0}
                ]
            }
        },
        {
            "description": "Valid JSON without markdown",
            "input": """{
        "points": [
            {"description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.", "score": 0}
        ]
    }""",
            "expected_output": """{
        "points": [
            {"description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.", "score": 0}
        ]
    }""",
            "expected_dict": {
                "points": [
                    {
                        "description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.",
                        "score": 0}
                ]
            }
        },
        {
            "description": "Malformed JSON with extra backslashes",
            "input": """```json
    {
        "points": [
            {"description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.", "score": 0}
        ]
    }""",
            "expected_output": """{
        "points": [
            {
                "description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.",
                "score": 0}
        ]
    }""",
            "expected_dict": {
                "points": [
                    {
                        "description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.",
                        "score": 0}
                ]
            }
        },
        {
            "description": "Valid JSON with line breaks",
            "input": """```json
            {
                "points": [
                    {
                        "description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.",
                        "score": 0}
                ]
            }
            ```""",
            "expected_output": """{
                "points": [
                    {
                        "description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.",
                        "score": 0}
                ]
            }""",
            "expected_dict": {
                "points": [
                    {
                        "description": "I don't know the answer to the user's question about the number of sports T-shirts used in the health run event.",
                        "score": 0}
                ]
            }
        }
    ]

    for case in test_cases:
        print(f"Running test: {case['description']}")
        cleaned_input, json_result = try_parse_json_object(case["input"])
        assert json_result == case[
            "expected_dict"], f"Test failed for input: {case['input']}. Expected: {case['expected_dict']}, but got: {json_result}"
        print(f"Test passed: {case['description']}")
