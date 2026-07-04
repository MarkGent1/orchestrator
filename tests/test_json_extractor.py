import json
import pytest

from utils.json_extractor import JsonExtractor


def test_extracts_plain_array():
    raw = '[{"file": "a.cs", "instructions": "create", "content": "x"}]'
    result = JsonExtractor.extract(raw)
    assert json.loads(result) == [{"file": "a.cs", "instructions": "create", "content": "x"}]


def test_extracts_array_from_markdown_fence():
    raw = '```json\n[{"file": "a.cs", "instructions": "create", "content": "x"}]\n```'
    result = JsonExtractor.extract(raw)
    assert json.loads(result) == [{"file": "a.cs", "instructions": "create", "content": "x"}]


def test_extracts_array_with_surrounding_prose():
    raw = 'Here is the plan:\n[{"file": "a.cs", "instructions": "create", "content": "x"}]\nLet me know if you need changes.'
    result = JsonExtractor.extract(raw)
    assert json.loads(result) == [{"file": "a.cs", "instructions": "create", "content": "x"}]


def test_bug1_brackets_inside_string_content_do_not_break_array_scan():
    """
    Regression test for the original crash: 'ValueError: No valid JSON
    array found'. A naive regex scanner treats '[' / ']' inside a JSON
    string value (e.g. a C# attribute like [ApiController]) as array
    boundaries. The bracket-depth scanner must track string state and
    ignore brackets inside quoted strings.
    """
    content = "[ApiController]\n[Route(\"users\")]\npublic class UsersController {}"
    raw = json.dumps([{"file": "UsersController.cs", "instructions": "create", "content": content}])
    result = JsonExtractor.extract(raw)
    parsed = json.loads(result)
    assert parsed[0]["content"] == content


def test_bug3_comments_in_structural_json_are_stripped_but_not_in_string_content():
    """
    Regression test for the third crash: naive comment-stripping
    corrupted "//" or "/* */" appearing inside code content strings.
    Comments must only be removed from the structural (non-string)
    parts of the payload, e.g. an actual trailing // comment after a
    JSON value, never from inside a "content" string that legitimately
    contains source code comments.
    """
    raw = (
        '[\n'
        '  {\n'
        '    "file": "a.cs",\n'
        '    "instructions": "create",\n'
        '    "content": "// this is a code comment\\n/* block */\\nvar x = 1;\\n"\n'
        '  } // trailing comment after the object\n'
        ']'
    )
    result = JsonExtractor.extract(raw)
    parsed = json.loads(result)
    assert parsed[0]["content"] == "// this is a code comment\n/* block */\nvar x = 1;\n"


def test_strips_trailing_commas_outside_strings():
    raw = '[{"file": "a.cs", "instructions": "create", "content": "x",},]'
    result = JsonExtractor.extract(raw)
    parsed = json.loads(result)
    assert parsed == [{"file": "a.cs", "instructions": "create", "content": "x"}]


def test_picks_first_valid_array_when_multiple_fences_present():
    raw = (
        '```json\n[{"file": "a.cs", "instructions": "create", "content": "x"}]\n```\n'
        'some prose\n'
        '```json\n[{"file": "b.cs", "instructions": "create", "content": "y"}]\n```'
    )
    result = JsonExtractor.extract(raw)
    parsed = json.loads(result)
    assert parsed[0]["file"] == "a.cs"


def test_raises_on_empty_input():
    with pytest.raises(ValueError):
        JsonExtractor.extract("")

    with pytest.raises(ValueError):
        JsonExtractor.extract("   ")


def test_raises_when_no_array_present():
    with pytest.raises(ValueError):
        JsonExtractor.extract("just some prose with no brackets at all")


def test_raises_when_only_unparseable_array_present():
    with pytest.raises(ValueError):
        JsonExtractor.extract("[this is not json at all, just [nested nonsense]]")


def test_already_valid_json_returned_untouched_fast_path():
    """
    Valid JSON should be returned as-is via the fast path rather than
    being rewritten by _clean_array, which would be a no-op here but
    should still not be reached/needed.
    """
    raw = '[{"file": "a.cs", "instructions": "create", "content": "no // fake comment here, real string"}]'
    result = JsonExtractor.extract(raw)
    assert json.loads(result)[0]["content"] == "no // fake comment here, real string"
