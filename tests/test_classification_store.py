import pytest
from llama_index.core.schema import TextNode
from pprint import pprint
from src.classification.classification_store import ClassificationIndexStore


@pytest.mark.parametrize(
    "test_case, store_data, expected_output",
    [
        (
            "empty",
            {
                "tree_schema": [],
                "tree_summary": {},
                "tree_path_summary": {},
                "tree": {},
                "nodes": [],
            },
            {
                "id": "root",
                "name": "root",
                "introduction": "",
                "subcategories": [],
                "documents": [],
            },
        ),
        (
            "empty with root summary",
            {
                "tree_schema": [],
                "tree_summary": {},
                "tree_path_summary": {
                    "": "summary-0",
                },
                "tree": {},
                "nodes": [
                    {
                        "id_": "summary-0",
                        "text": "root summary",
                    },
                ],
            },
            {
                "id": "root",
                "name": "root",
                "introduction": "root summary",
                "subcategories": [],
                "documents": [],
            },
        ),
        (
            "single branch",
            {
                "tree_schema": [
                    "Business",
                ],
                "tree_summary": {
                    "Business": "summary-0",
                },
                "tree_path_summary": {
                    "": "summary-2",
                },
                "tree": {
                    "Business": [
                        "doc-0"
                    ],
                },
                "nodes": [
                    {
                        "id_": "summary-0",
                        "text": "intro to business category",
                    },
                    {
                        "id_": "summary-2",
                        "text": "root summary",
                    },
                    {
                        "id_": "doc-0",
                        "metadata": {
                            "title": "Chevron Company Profile",
                        },
                        "text": "# Chevron Company Profile\n## Stock Performance\n*...\n",
                    },
                ],
            },
            {
                "id": "root",
                "name": "root",
                "introduction": "root summary",
                "documents": [],
                "subcategories": [
                    {
                        "id": "root - Business",
                        "name": "Business",
                        "introduction": "intro to business category",
                        "subcategories": [
                        ],
                        "documents": [
                            {
                                "id": "doc-0",
                                "title": "Chevron Company Profile",
                                "summary": "# Chevron Company Profile\n## Stock Performance\n*...\n",
                            }
                        ]
                    },
                ],
            }
        ),
        (
            "complex",
            {
                "tree_schema": [
                    "Business",
                    "Computer Science - Artificial Intelligence",
                ],
                "tree_summary": {
                    "Business": "summary-0",
                    "Computer Science - Artificial Intelligence": "summary-1",
                },
                "tree_path_summary": {
                    "": "summary-2",
                    "Computer Science": "summary-3",
                },
                "tree": {
                    "Business": [
                        "doc-0"
                    ],
                    "Computer Science - Artificial Intelligence": [
                        "doc-1"
                    ],
                },
                "nodes": [
                    {
                        "id_": "summary-0",
                        "text": "intro to business category",
                    },
                    {
                        "id_": "summary-1",
                        "text": "intro to AI category",
                    },
                    {
                        "id_": "summary-2",
                        "text": "root summary",
                    },
                    {
                        "id_": "summary-3",
                        "text": "intro to computer science",
                    },
                    {
                        "id_": "doc-0",
                        "metadata": {
                            "title": "Chevron Company Profile",
                        },
                        "text": "# Chevron Company Profile\n## Stock Performance\n*...\n",
                    },
                    {
                        "id_": "doc-1",
                        "metadata": {
                            "title": "Variance Reduced Meta-CL (VR-MCL)",
                        },
                        "text": "# Variance Reduced Meta-CL (VR-MCL)\n### Authors\nxxx...\n",
                    },
                ],
            },
            {
                "id": "root",
                "name": "root",
                "introduction": "root summary",
                "documents": [],
                "subcategories": [
                    {
                        "id": "root - Business",
                        "name": "Business",
                        "introduction": "intro to business category",
                        "subcategories": [
                        ],
                        "documents": [
                            {
                                "id": "doc-0",
                                "title": "Chevron Company Profile",
                                "summary": "# Chevron Company Profile\n## Stock Performance\n*...\n",
                            }
                        ]
                    },
                    {
                        "id": "root - Computer Science",
                        "name": "Computer Science",
                        "introduction": "intro to computer science",
                        "documents": [],
                        "subcategories": [
                            {
                                "id": "root - Computer Science - Artificial Intelligence",
                                "name": "Artificial Intelligence",
                                "introduction": "intro to AI category",
                                "subcategories": [],
                                "documents": [
                                    {
                                        "id": "doc-1",
                                        "title": "Variance Reduced Meta-CL (VR-MCL)",
                                        "summary": "# Variance Reduced Meta-CL (VR-MCL)\n### Authors\nxxx...\n",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ),
    ]
)
def test_get_category_tree(test_case, store_data, expected_output):
    if test_case == "pass":
        return

    store = ClassificationIndexStore()
    store._tree_schema = store_data["tree_schema"]
    store._tree_summary = store_data["tree_summary"]
    store._tree_path_summary = store_data["tree_path_summary"]
    store._tree = store_data["tree"]
    store._nodes = [TextNode(**node) for node in store_data["nodes"]]
    result = store.get_category_tree()
    print("result:")
    pprint(result)
    print("expected_output:")
    pprint(expected_output)
    assert expected_output == result, f"Test case {test_case} failed"
