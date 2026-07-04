import json

from utils.json_sanitizer import JsonSanitizer


def test_returns_already_valid_json_untouched():
    """
    Regression test for the sanitizer double-escape bug: previously,
    sanitize() unconditionally re-escaped quotes inside "content"
    fields even when the input already parsed as valid JSON, which
    corrupted already-correct escaped quotes (e.g. C# attributes like
    [Route("users")]) into double-escaped garbage.
    """
    valid = json.dumps([{
        "file": "UsersController.cs",
        "instructions": "create",
        "content": 'using Microsoft.AspNetCore.Mvc;\n\n[ApiController]\n[Route("users")]\npublic class UsersController {}\n',
    }])
    result = JsonSanitizer.sanitize(valid)
    assert result == valid
    assert json.loads(result)[0]["content"].count('"users"') == 1


def test_collapses_broken_backslash_control_char_sequences():
    """
    sanitize() repairs literal backslash+newline/tab/CR sequences
    (invalid as raw JSON string escapes) down to the plain control
    character. This alone doesn't guarantee valid JSON -- a raw
    control character inside a JSON string is still technically
    non-conformant -- so this checks the substitution directly rather
    than requiring json.loads to succeed on this synthetic fragment.
    """
    text = "a\\\nb\\\tc\\\rd"
    result = JsonSanitizer.sanitize(text)
    assert result == "a\nb\tc\rd"


def test_sanitize_is_idempotent_on_valid_json():
    valid = '[{"file": "a.cs", "instructions": "create", "content": "hello"}]'
    once = JsonSanitizer.sanitize(valid)
    twice = JsonSanitizer.sanitize(once)
    assert once == twice == valid
