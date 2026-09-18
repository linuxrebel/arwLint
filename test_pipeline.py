#!/usr/bin/env python3
"""Unit tests for the in-plugin fix pipeline's pure movers.

No model, no ollama — just the deterministic parts (_clean_proposal,
_apply_insert). The live /lint run stays a manual smoke, not a standing test.
"""
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location(
    "arwlint_plugin", pathlib.Path(__file__).with_name("plugin.py"))
mod = importlib.util.module_from_spec(spec)
mod.__dict__["resolve_abs_path"] = lambda p: pathlib.Path(p)
mod.__dict__["PLUGIN_DIR"] = pathlib.Path(__file__).parent
spec.loader.exec_module(mod)


def test_clean_proposal_strips_fence_and_backticks():
    assert mod._clean_proposal("```\n    x = 1\n```") == "    x = 1"
    assert mod._clean_proposal('`"""doc"""`') == '"""doc"""'
    assert mod._clean_proposal("nope\nnope") == ""        # >1 line => ""
    assert mod._clean_proposal("UNFIXABLE") == ""
    print("  _clean_proposal strips fences/backticks/UNFIXABLE   ok")


def test_apply_insert_shebang_goes_below_line1():
    lines = ["#!/usr/bin/env python3\n", "x=1\n"]
    f = {"action_kind": "insert_top", "line": 1}
    out = mod._apply_insert(lines, f, '"""mod."""')
    assert out[0] == "#!/usr/bin/env python3\n"
    assert out[1].strip() == '"""mod."""'
    print("  _apply_insert keeps shebang on line 1              ok")


if __name__ == "__main__":
    test_clean_proposal_strips_fence_and_backticks()
    test_apply_insert_shebang_goes_below_line1()
    print("all arwLint pipeline tests passed")
