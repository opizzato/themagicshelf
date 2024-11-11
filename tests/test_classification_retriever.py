import pytest
from unittest.mock import MagicMock

from src.classification.classification_retriever import ClassificationRetriever


@pytest.mark.parametrize(
    "test_case, input_str, expected_output",
    [
        ("empty", "", None),
        ("full", """
hierarchical_classification_locations:
- Technology - AI, score:80
- Technology - Gadgets, score:60
tags:
- Informative, score:90
- Recent, score:80""", {
            'locations': [
                {'location': 'Technology - AI', 'score': 80}, 
                {'location': 'Technology - Gadgets', 'score': 60}
            ],
            'tags': [
                {'tag': 'Informative', 'score': 90}, 
                {'tag': 'Recent', 'score': 80}
            ]}), 
        ("empty_locations", """
tags:
- Informative, score:90
- Recent, score:80""", None),
        ("empty_tags", """
hierarchical_classification_locations:
- Technology - AI, score:80
- Technology - Gadgets, score:60
""", None),
    ]
)
def test_parse_locations_and_tags(test_case, input_str, expected_output):
    retriever = ClassificationRetriever(store=MagicMock(), llm=MagicMock())

    result = retriever._parse_locations_and_tags(input_str)
    assert result == expected_output, f"Test case {test_case} failed"