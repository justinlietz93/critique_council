"""
Mock o3-mini API responses for testing.

This module contains specific mock responses for the o3-mini model for use in tests.
"""

# Successful o3-mini response
O3_MINI_SUCCESS = {
    "output": [
        {"role": "assistant", "content": [{"text": """
{
  "points": [
    {
      "id": "point-1",
      "point": "First point from o3-mini"
    },
    {
      "id": "point-2",
      "point": "Second point from o3-mini"
    }
  ]
}
"""}]}
    ]
}

# Truncated o3-mini response (seen in logs)
O3_MINI_TRUNCATED = {
    "output": [
        {"role": "assistant", "content": [{"text": """
{
  "points": [
    {
      "id": "point-1",
      "point": "First point from o3-mini"
    },
    {
"""}]}
    ]
}

# Non-JSON o3-mini response
O3_MINI_NON_JSON = {
    "output": [
        {"role": "assistant", "content": [{"text": """
I've analyzed the content and extracted the following key points:

1. First point from o3-mini
2. Second point from o3-mini
3. Third point from o3-mini
"""}]}
    ]
}
