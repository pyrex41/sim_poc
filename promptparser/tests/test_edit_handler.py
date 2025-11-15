from app.services.edit_handler import merge_iterative_edit


def test_merge_iterative_edit_adds_note():
    previous = {"creative_direction": {"product": {"name": "watch"}}}
    merged = merge_iterative_edit(previous, "make it faster")
    assert "iteration_notes" in merged["metadata"]
    assert "make it faster" in merged["metadata"]["iteration_notes"][0]

