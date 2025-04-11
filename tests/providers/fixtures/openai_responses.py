"""
Mock OpenAI API responses for testing.

This module contains mock responses for the OpenAI API for use in tests.
"""

# General successful response
SUCCESSFUL_RESPONSE = {
    "points": [
        {"id": "point-1", "point": "First test point"},
        {"id": "point-2", "point": "Second test point"}
    ]
}

# Incomplete JSON response (missing closing braces/brackets)
INCOMPLETE_JSON_RESPONSE = """
{
  "points": [
    {
      "id": "point-1",
      "point": "First point"
    },
    {
      "id": "point-2",
      "point": "Second point"
    }
"""

# Malformed JSON response
MALFORMED_JSON_RESPONSE = """
{
  "points": [
    {
      "id": "point-1",
      "point": "First point"
    },
    {
      "id": "point-2"
      "point": "Second point with syntax error - missing comma"
    }
  ]
}
"""

# Non-JSON text response
TEXT_RESPONSE = """
Here are some points:
1. First point from text
2. Second point from text
3. Third point from text
"""

# Empty response
EMPTY_RESPONSE = ""
