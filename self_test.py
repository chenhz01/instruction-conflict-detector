# -*- coding: utf-8 -*-
"""self_test for instruction-conflict-detector — R14, inherits 4-defence template v2.

Defence 2 note: unicode rule fixtures verified without ASCII-only \\w matching.
"""
import atexit
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instruction_conflict_detector as m  # noqa: E402

_TMP = tempfile.mkdtemp(prefix="icd_selftest_")
atexit.register(shutil.rmtree, _TMP, ignore_errors=True)


def wf(name, content):
    p = os.path.join(_TMP, name)
    with open(p, "w", encoding="utf-8", newline="") as f:  # Defence 3
        f.write(content)
    return p


def run_cli(argv):
    buf_out, buf_err = io.StringIO(), io.StringIO()
    code = 0
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            m.main(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except Exception as e:  # noqa: BLE001
        code = 1
        buf_err.write(repr(e))
    return code, buf_out.getvalue(), buf_err.getvalue()


CLEAN_PROMPT = "\n".join([
    "1. Always answer in English.",
    "2. Keep responses under 200 words.",
    "3. Use markdown tables for data.",
])
CONFLICT_PROMPT = "\n".join([
    "1. Always answer in English.",
    "2. Never answer in English.",
    "3. Keep responses short.",
])
OVERRIDE_LINEAR = "\n".join([
    "1. Always answer in English.",
    "2. Keep responses short.",
    "3. Use markdown tables for data.",
    "Rule 1 overrides Rule 2.",
])
OVERRIDE_CYCLE = "\n".join([
    "1. Always answer in English.",
    "2. Never answer in English.",
    "3. Always answer in French.",
    "Rule 1 overrides Rule 2.",
    "Rule 2 overrides Rule 3.",
    "Rule 3 overrides Rule 1.",
])
FILE_CLEAN = wf("clean.txt", CLEAN_PROMPT)
FILE_CONFLICT = wf("conflict.txt", CONFLICT_PROMPT)

# ---- [A] functional ----
A_CASES = []


def _a(name):
    def deco(fn):
        A_CASES.append((name, fn))
        return fn
    return deco


@_a("clean_prompt_no_errors")
def _(s):
    s.assertEqual([f for f in m.analyze_rules(CLEAN_PROMPT)
                   if f["severity"] == "ERROR"], [])


@_a("direct_conflict_detected")
def _(s):
    s.assertTrue(any(f["code"] == "DIRECT_CONFLICT"
                     for f in m.analyze_rules(CONFLICT_PROMPT)))


@_a("conflict_reversed_order")
def _(s):
    text = "1. Never answer in English.\n2. Always answer in English.\n"
    s.assertTrue(any(f["code"] == "DIRECT_CONFLICT" for f in m.analyze_rules(text)))


@_a("duplicate_rules_warn")
def _(s):
    text = "1. Always answer in English.\n2. Always answer in English.\n"
    s.assertTrue(any(f["code"] == "DUPLICATE_RULE" for f in m.analyze_rules(text)))


@_a("undeclared_priority_info")
def _(s):
    text = "1. Keep responses short.\n2. Keep responses short and simple.\n"
    s.assertTrue(any(f["code"] == "UNDECLARED_PRIORITY"
                     for f in m.analyze_rules(text)))


@_a("priority_marker_suppresses_info")
def _(s):
    text = "1. Keep responses short.\n2. Keep responses under 100 words; the first rule takes precedence.\n"
    s.assertEqual([f for f in m.analyze_rules(text)
                   if f["code"] == "UNDECLARED_PRIORITY"], [])


@_a("linear_override_no_error")
def _(s):
    s.assertEqual([f for f in m.analyze_rules(OVERRIDE_LINEAR)
                   if f["severity"] == "ERROR"], [])


@_a("three_node_cycle_detected")
def _(s):
    s.assertTrue(any(f["code"] == "CIRCULAR_OVERRIDE"
                     for f in m.analyze_rules(OVERRIDE_CYCLE)))


@_a("two_node_cycle_detected")
def _(s):
    text = "1. Always answer in English.\n2. Never answer in English.\nRule 1 overrides Rule 2.\nRule 2 overrides Rule 1.\n"
    s.assertTrue(any(f["code"] == "CIRCULAR_OVERRIDE" for f in m.analyze_rules(text)))


@_a("unknown_rule_ref")
def _(s):
    text = "1. Always answer in English.\nRule 9 overrides Rule 2.\n"
    s.assertTrue(any(f["code"] == "UNKNOWN_RULE_REF" for f in m.analyze_rules(text)))


@_a("empty_text_no_rules")
def _(s):
    s.assertEqual([f["code"] for f in m.analyze_rules("")], ["NO_RULES"])


@_a("vague_rule_flagged")
def _(s):
    s.assertTrue(any(f["code"] == "VAGUE_RULE"
                     for f in m.analyze_rules("1. Do it.\n")))


@_a("parse_numbered_count")
def _(s):
    s.assertEqual(len(m.parse_rules(CLEAN_PROMPT)), 3)


@_a("parse_bullet_count")
def _(s):
    s.assertEqual(len(m.parse_rules("- alpha rule here\n- beta rule here\n")), 2)


@_a("parse_paren_numbering")
def _(s):
    s.assertEqual(len(m.parse_rules("1) alpha rule here\n2) beta rule here\n")), 2)


@_a("unicode_rules_parse")
def _(s):
    rules = m.parse_rules("1. 永远用中文回答。\n2. 不要用中文回答。\n")
    s.assertEqual(len(rules), 2)
    s.assertIsInstance(m.analyze_rules(
        "1. 永远用中文回答。\n2. 不要用中文回答。\n"), list)


@_a("same_modality_no_conflict")
def _(s):
    text = "1. Always answer in English.\n2. Always answer in French.\n"
    s.assertEqual([f for f in m.analyze_rules(text)
                   if f["code"] == "DIRECT_CONFLICT"], [])


@_a("negative_negative_no_conflict")
def _(s):
    text = "1. Never mention pricing.\n2. Never mention competitors.\n"
    s.assertEqual([f for f in m.analyze_rules(text)
                   if f["code"] == "DIRECT_CONFLICT"], [])


@_a("conflict_message_has_rules")
def _(s):
    fs = m.analyze_rules(CONFLICT_PROMPT)
    msg = [f["message"] for f in fs if f["code"] == "DIRECT_CONFLICT"][0]
    self_msg = msg
    s.assertIn("rules 1 and 2", self_msg)


@_a("conflict_severity_error")
def _(s):
    fs = m.analyze_rules(CONFLICT_PROMPT)
    s.assertEqual([f for f in fs if f["code"] == "DIRECT_CONFLICT"][0]["severity"], "ERROR")


@_a("two_conflict_pairs_both_reported")
def _(s):
    text = "1. Always answer in English.\n2. Never answer in English.\n" \
           "3. Always use formal tone.\n4. Never use formal tone.\n"
    s.assertEqual(len([f for f in m.analyze_rules(text)
                       if f["code"] == "DIRECT_CONFLICT"]), 2)


@_a("self_override_cycle")
def _(s):
    text = "1. Always answer in English.\nRule 1 overrides Rule 1.\n"
    s.assertTrue(any(f["code"] == "CIRCULAR_OVERRIDE" for f in m.analyze_rules(text)))


@_a("precedence_keyword_edge")
def _(s):
    text = "1. Always answer in English.\n2. Never answer in English.\nRule 1 precedes Rule 2.\n"
    s.assertEqual([f for f in m.analyze_rules(text)
                   if f["code"] in ("UNKNOWN_RULE_REF", "CIRCULAR_OVERRIDE")], [])


@_a("no_rules_severity_info")
def _(s):
    s.assertEqual(m.analyze_rules("plain prose without bullets")[0]["severity"], "INFO")


@_a("prose_without_bullets_no_rules")
def _(s):
    s.assertEqual(m.analyze_rules("You are a helpful assistant.")[0]["code"], "NO_RULES")


class TestA(unittest.TestCase):
    pass


for _i, (_nm, _fn) in enumerate(A_CASES):
    setattr(TestA, "test_a%02d_%s" % (_i, _nm), _fn)

# ---- [B] CLI contract ----
B_CASES = [
    ("clean_exit0", [FILE_CLEAN], 0, "", ""),
    ("conflict_exit1", [FILE_CONFLICT], 1, "DIRECT_CONFLICT", ""),
    ("json_flag", [FILE_CLEAN, "--json"], 0, '"findings"', ""),
    ("missing_file", [os.path.join(_TMP, "absent.txt")], 2, "", "cannot read"),
    ("min_shared_suppresses", [FILE_CLEAN, "--min-shared", "99"], 0, "", ""),
    ("text_output_summary", [FILE_CLEAN], 0, "summary:", ""),
    ("json_summary_key", [FILE_CONFLICT, "--json"], 1, '"summary"', ""),
]


def _mk_b(name, argv, code, out_sub="", err_sub=""):
    def t(self):
        c, out, err = run_cli(argv)
        self.assertEqual(c, code, msg="out=%r err=%r" % (out, err))
        if out_sub:
            self.assertIn(out_sub, out)
        if err_sub:
            self.assertIn(err_sub, err)
    t.__doc__ = "B: %s" % name
    return t


class TestB(unittest.TestCase):
    def test_b7_missing_positional(self):
        c, _out, _err = run_cli([])
        self.assertEqual(c, 2)

    def test_b8_help_exit0(self):
        c, out, _err = run_cli(["--help"])
        self.assertEqual(c, 0)
        self.assertIn("usage:", out)

    def test_b9_json_roundtrip(self):
        c, out, _err = run_cli([FILE_CONFLICT, "--json"])
        self.assertEqual(c, 1)
        data = json.loads(out)
        self.assertTrue(any(f["code"] == "DIRECT_CONFLICT" for f in data["findings"]))


for _i, (_nm, _av, _cd, _os, _es) in enumerate(B_CASES):
    setattr(TestB, "test_b%02d_%s" % (_i, _nm), _mk_b(_nm, _av, _cd, _os, _es))

# ---- [C] extreme/edge ----
C_CASES = [
    ("empty_string", lambda s: s.assertEqual(
        [f["code"] for f in m.analyze_rules("")], ["NO_RULES"])),
    ("whitespace_only", lambda s: s.assertEqual(
        m.analyze_rules("   \n\t  ")[0]["code"], "NO_RULES")),
    ("huge_text_completes", lambda s: s.assertIsInstance(
        m.analyze_rules("1. Always answer in English.\n" * 2000), list)),
    ("thousand_rules_completes", lambda s: s.assertEqual(
        len(m.parse_rules("\n".join("%d. rule number %d here" % (i + 1, i + 1)
                                    for i in range(1000)) + "\n")), 1000)),
    ("crlf_prompt", lambda s: s.assertTrue(any(
        f["code"] == "DIRECT_CONFLICT"
        for f in m.analyze_rules(CONFLICT_PROMPT.replace("\n", "\r\n"))))),
    ("tab_bullet_parsed", lambda s: s.assertEqual(
        len(m.parse_rules("\t- alpha rule here\n")), 1)),
    ("emoji_in_rule", lambda s: s.assertIsInstance(
        m.analyze_rules("1. Always answer with 🎉 when happy.\n"), list)),
    ("dup_normalized_whitespace", lambda s: s.assertTrue(any(
        f["code"] == "DUPLICATE_RULE" for f in m.analyze_rules(
            "1. Always answer in English.\n2. Always   answer in English.\n")))),
    ("dup_triple_three_findings", lambda s: s.assertEqual(
        len([f for f in m.analyze_rules(
            "1. Always answer in English.\n2. Always answer in English.\n"
            "3. Always answer in English.\n") if f["code"] == "DUPLICATE_RULE"]), 3)),
    ("dont_contraction_negative", lambda s: s.assertTrue(any(
        f["code"] == "DIRECT_CONFLICT" for f in m.analyze_rules(
            "1. Always answer in English.\n2. Don't answer in English.\n")))),
    ("uppercase_modality", lambda s: s.assertTrue(any(
        f["code"] == "DIRECT_CONFLICT" for f in m.analyze_rules(
            "1. ALWAYS answer in English.\n2. NEVER answer in English.\n")))),
    ("override_case_insensitive", lambda s: s.assertTrue(any(
        f["code"] in ("CIRCULAR_OVERRIDE",) for f in m.analyze_rules(
            "1. Always answer in English.\n2. Never answer in English.\n"
            "rule 1 OVERRIDES rule 2.\nrule 2 overrides rule 1.\n")))),
    ("mixed_explicit_numbers", lambda s: s.assertTrue(any(
        f["code"] == "UNKNOWN_RULE_REF" for f in m.analyze_rules(
            "10. Always answer in English.\nRule 5 overrides Rule 2.\n")))),
    ("heading_lines_ignored", lambda s: s.assertEqual(
        len(m.parse_rules("## Policies\n\n1. Always answer in English.\n")), 1)),
    ("none_raises", lambda s: s.assertRaises(TypeError, m.analyze_rules, None)),
    ("int_raises", lambda s: s.assertRaises(TypeError, m.analyze_rules, 42)),
    ("vague_does_not_fail_cli", lambda s: s.assertEqual(
        run_cli([wf("c_vague.txt", "1. Do it.\n")])[0], 0)),
    ("single_rule_no_pairs", lambda s: s.assertEqual(
        [f for f in m.analyze_rules("1. Always answer in English.\n")
         if f["code"] in ("DIRECT_CONFLICT", "UNDECLARED_PRIORITY", "DUPLICATE_RULE")], [])),
    ("conflict_survives_priority_marker", lambda s: s.assertTrue(any(
        f["code"] == "DIRECT_CONFLICT" for f in m.analyze_rules(
            "1. Always answer in English.\n2. Never answer in English; "
            "this rule wins.\n")))),
    ("min_shared_one_flags_priority", lambda s: s.assertTrue(any(
        f["code"] == "UNDECLARED_PRIORITY" for f in m.analyze_rules(
            "1. Keep answers brief.\n2. Keep answers friendly.\n", min_shared=1)))),
    ("parse_none_raises", lambda s: s.assertRaises(TypeError, m.parse_rules, None)),
    ("keywords_unicode", lambda s: s.assertEqual(
        m.keywords("永远用中文回答"), {"永远用中文回答"})),
    ("modality_mixed_neg_wins", lambda s: s.assertEqual(
        m.modality("Never use formal tone unless asked"), "negative")),
    ("neutral_rule", lambda s: s.assertEqual(
        m.modality("Answer the user question"), "neutral")),
    ("cli_directory_exit2", lambda s: s.assertEqual(run_cli([_TMP])[0], 2)),
]


class TestC(unittest.TestCase):
    pass


for _i, (_nm, _fn) in enumerate(C_CASES):
    setattr(TestC, "test_c%02d_%s" % (_i, _nm), _fn)


# ---- Round-2 additions (v0.1.1): extra extreme-edge coverage ----
class TestR2(unittest.TestCase):
    def test_r2_many_duplicates_all_pairs(self):
        text = "".join("%d. Always answer in English.\n" % (i + 1) for i in range(500))
        fs = m.analyze_rules(text)
        self.assertEqual(len([f for f in fs if f["code"] == "DUPLICATE_RULE"]), 500 * 499 // 2)

    def test_r2_numeric_only_rule_vague(self):
        fs = m.analyze_rules("1. 123 456.\n")
        self.assertEqual([f["code"] for f in fs], ["VAGUE_RULE"])

    def test_r2_four_node_cycle(self):
        text = "\n".join(["%d. Point %d of policy." % (i, i) for i in range(1, 5)] +
                         ["Rule 1 overrides Rule 2.", "Rule 2 overrides Rule 3.",
                          "Rule 3 overrides Rule 4.", "Rule 4 overrides Rule 1."])
        self.assertTrue(any(f["code"] == "CIRCULAR_OVERRIDE" for f in m.analyze_rules(text)))

    def test_r2_min_shared_3_suppresses(self):
        fs = m.analyze_rules("1. Keep responses short.\n2. Keep responses short and simple.\n",
                             min_shared=3)
        self.assertEqual([f for f in fs if f["code"] == "UNDECLARED_PRIORITY"], [])

if __name__ == "__main__":
    r = unittest.TextTestRunner(verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules["__main__"]))
    total, fails = r.testsRun, len(r.failures) + len(r.errors)
    print("SUMMARY: PASS %d/%d" % (total - fails, total))  # Defence 4
    sys.exit(0 if fails == 0 else 1)
