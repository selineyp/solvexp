import pytest
from unittest.mock import patch
from solvexp.src.framework import ArgumentationFramework, Arg


def make_fw(args: list[Arg], attacks: dict[Arg, list[Arg]]) -> ArgumentationFramework:
    return ArgumentationFramework(arguments=frozenset(args), attacks=attacks)


# ---------------------------------------------------------------------------
# computeStableExtension
# ---------------------------------------------------------------------------

class TestComputeStableExtension:
    def test_empty_framework(self):
        fw = make_fw([], {})
        with patch("solvexp.src.framework.compute_stable_extension", return_value=set()):
            assert fw.computeStableExtension() == frozenset()

    def test_single_unattacked_arg(self):
        a = ("m1", "w1")
        fw = make_fw([a], {})
        with patch("solvexp.src.framework.compute_stable_extension", return_value={"m1:w1"}):
            assert fw.computeStableExtension() == frozenset([a])

    def test_no_stable_extension_returns_empty(self):
        a = ("a", "1")
        fw = make_fw([a], {a: [a]})  # self-attack
        with patch("solvexp.src.framework.compute_stable_extension", return_value=set()):
            assert fw.computeStableExtension() == frozenset()

    def test_passes_correct_args_and_attacks_to_solver(self):
        a, b, c = ("m1", "w1"), ("m1", "w2"), ("m1", "w3")
        fw = make_fw([a, b, c], {a: [b], b: [c]})
        with patch("solvexp.src.framework.compute_stable_extension", return_value={"m1:w1", "m1:w3"}) as mock:
            fw.computeStableExtension()
            call_args, call_attacks = mock.call_args[0]
            assert set(call_args) == {"m1:w1", "m1:w2", "m1:w3"}
            assert call_attacks == {"m1:w1": ["m1:w2"], "m1:w2": ["m1:w3"]}

    def test_result_converted_back_to_arg_tuples(self):
        a, b = ("x", "y"), ("p", "q")
        fw = make_fw([a, b], {a: [b]})
        with patch("solvexp.src.framework.compute_stable_extension", return_value={"x:y"}):
            result = fw.computeStableExtension()
            assert result == frozenset([a])

    def test_mutual_attack(self):
        a, b = ("a", "1"), ("b", "1")
        fw = make_fw([a, b], {a: [b], b: [a]})
        with patch("solvexp.src.framework.compute_stable_extension", return_value={"a:1"}):
            assert fw.computeStableExtension() == frozenset([a])


# ---------------------------------------------------------------------------
# isAcceptable
# ---------------------------------------------------------------------------

class TestIsAcceptable:
    def test_no_attackers_always_acceptable(self):
        a = ("a", "1")
        fw = make_fw([a], {})
        assert fw.isAcceptable(a, frozenset()) is True

    def test_attacker_countered_by_argset(self):
        a, b, c = ("a", "1"), ("b", "1"), ("c", "1")
        # b attacks a; c attacks b → a is acceptable to {c}
        fw = make_fw([a, b, c], {b: [a], c: [b]})
        assert fw.isAcceptable(a, frozenset([c])) is True

    def test_attacker_not_countered(self):
        a, b = ("a", "1"), ("b", "1")
        # b attacks a; nothing counters b → a not acceptable to {}
        fw = make_fw([a, b], {b: [a]})
        assert fw.isAcceptable(a, frozenset()) is False

    def test_unrelated_attacks_do_not_affect_acceptability(self):
        a, b, c = ("a", "1"), ("b", "1"), ("c", "1")
        # b attacks c only; a has no attackers
        fw = make_fw([a, b, c], {b: [c]})
        assert fw.isAcceptable(a, frozenset()) is True

    def test_arg_acceptable_to_itself_if_it_counters_its_attacker(self):
        a, b = ("a", "1"), ("b", "1")
        # a attacks b, b attacks a → a is acceptable to {a}
        fw = make_fw([a, b], {a: [b], b: [a]})
        assert fw.isAcceptable(a, frozenset([a])) is True


# ---------------------------------------------------------------------------
# fixedPointOperator
# ---------------------------------------------------------------------------

class TestFixedPointOperator:
    def test_no_attacks_all_args_acceptable(self):
        a, b = ("a", "1"), ("b", "1")
        fw = make_fw([a, b], {})
        assert fw.fixedPointOperator(frozenset()) == frozenset([a, b])

    def test_empty_arguments(self):
        fw = make_fw([], {})
        assert fw.fixedPointOperator(frozenset()) == frozenset()

    def test_chain_fixed_point_of_empty_set(self):
        a, b, c = ("a", "1"), ("b", "1"), ("c", "1")
        # a→b→c: only a has no attackers, so F({}) = {a}
        fw = make_fw([a, b, c], {a: [b], b: [c]})
        assert fw.fixedPointOperator(frozenset()) == frozenset([a])

    def test_chain_fixed_point_of_a(self):
        a, b, c = ("a", "1"), ("b", "1"), ("c", "1")
        # a→b→c: F({a}) = {a, c} since b is attacked by a (so c's attacker is countered)
        fw = make_fw([a, b, c], {a: [b], b: [c]})
        assert fw.fixedPointOperator(frozenset([a])) == frozenset([a, c])

    def test_mutual_attack_fixed_point_of_empty(self):
        a, b = ("a", "1"), ("b", "1")
        # a↔b: neither is acceptable to {} (each is attacked by the other, uncountered)
        fw = make_fw([a, b], {a: [b], b: [a]})
        assert fw.fixedPointOperator(frozenset()) == frozenset()


# ---------------------------------------------------------------------------
# getExplanation
# ---------------------------------------------------------------------------

class TestGetExplanation:
    def test_returns_string(self):
        a, b = ("a", "1"), ("b", "1")
        fw = make_fw([a, b], {b: [a]})
        result = fw.getExplanation(frozenset([b]), a)
        assert isinstance(result, str)

    def test_mentions_arg_in_output(self):
        a, b = ("a", "1"), ("b", "1")
        fw = make_fw([a, b], {b: [a]})
        result = fw.getExplanation(frozenset([b]), a)
        assert str(a) in result

    def test_mentions_attacker(self):
        a, b = ("a", "1"), ("b", "1")
        fw = make_fw([a, b], {b: [a]})
        result = fw.getExplanation(frozenset([b]), a)
        assert str(b) in result

    def test_no_attackers_returns_header_only(self):
        a = ("a", "1")
        fw = make_fw([a], {})
        result = fw.getExplanation(frozenset([a]), a)
        assert str(a) in result
        # no attacker lines expected
        assert "attacked by" not in result
