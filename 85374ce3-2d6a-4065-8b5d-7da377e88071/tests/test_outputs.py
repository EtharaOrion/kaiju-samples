"""Behavioral tests for the neat-python re-implementation.

These tests import the real solution modules and assert on concrete
behavior drawn from the TRUTH.md contract. They are designed to pass on a
correct implementation and fail on a stub/broken one.
"""
import math
import pytest


# ---------------------------------------------------------------------------
# Activation functions
# ---------------------------------------------------------------------------










# ---------------------------------------------------------------------------
# Aggregation functions
# ---------------------------------------------------------------------------








# ---------------------------------------------------------------------------
# Math utilities
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Attributes
# ---------------------------------------------------------------------------
def _float_config(**overrides):
    cfg = {
        'x_init_mean': 0.0,
        'x_init_stdev': 1.0,
        'x_init_type': 'gaussian',
        'x_replace_rate': 0.0,
        'x_mutate_rate': 0.0,
        'x_mutate_power': 1.0,
        'x_max_value': 30.0,
        'x_min_value': -30.0,
    }
    cfg.update(overrides)
    return cfg






















# ---------------------------------------------------------------------------
# Genes
# ---------------------------------------------------------------------------


def test_activation_pinned_values():
    from neat.activations import (
        sigmoid_activation, tanh_activation, sin_activation,
        gauss_activation, relu_activation, identity_activation,
        clamped_activation, square_activation, cube_activation,
        abs_activation, hat_activation, exp_activation, log_activation,
        softplus_activation, inv_activation,
    )
    # tanh
    assert tanh_activation(0.0) == pytest.approx(0.0)
    assert tanh_activation(1.0) == pytest.approx(math.tanh(2.5))
    assert tanh_activation(-1.0) == pytest.approx(math.tanh(-2.5))
    # sin
    assert sin_activation(0.0) == pytest.approx(0.0)
    assert sin_activation(1.0) == pytest.approx(math.sin(5.0))
    # gauss peaks at 1.0 at zero
    assert gauss_activation(0.0) == pytest.approx(1.0)
    assert gauss_activation(1.0) == pytest.approx(math.exp(-5.0))
    # relu
    assert relu_activation(2.0) == pytest.approx(2.0)
    assert relu_activation(-2.0) == pytest.approx(0.0)
    # identity
    assert identity_activation(3.14) == pytest.approx(3.14)
    # clamped
    assert clamped_activation(5.0) == pytest.approx(1.0)
    assert clamped_activation(-5.0) == pytest.approx(-1.0)
    assert clamped_activation(0.5) == pytest.approx(0.5)
    # square/cube/abs
    assert square_activation(3.0) == pytest.approx(9.0)
    assert cube_activation(2.0) == pytest.approx(8.0)
    assert abs_activation(-4.0) == pytest.approx(4.0)
    # hat: max(0, 1-|z|)
    assert hat_activation(0.0) == pytest.approx(1.0)
    assert hat_activation(2.0) == pytest.approx(0.0)
    assert hat_activation(0.5) == pytest.approx(0.5)
    # sigmoid logistic on 5z
    assert sigmoid_activation(0.0) == pytest.approx(0.5)
    assert 0.0 < sigmoid_activation(1.0) < 1.0
    # exp/log
    assert exp_activation(0.0) == pytest.approx(1.0)
    assert log_activation(1.0) == pytest.approx(0.0)
    # softplus at 0: 0.2*log(2)
    assert softplus_activation(0.0) == pytest.approx(0.2 * math.log(2.0))
    # inv reciprocal
    assert inv_activation(2.0) == pytest.approx(0.5)

def test_activation_inv_arithmetic_error():
    from neat.activations import inv_activation
    # division by zero must be caught and yield 0.0
    assert inv_activation(0.0) == pytest.approx(0.0)

def test_activation_log_floor():
    from neat.activations import log_activation
    # non-positive arg floored to 1e-7 -> finite value
    v = log_activation(0.0)
    assert math.isfinite(v)

def test_activation_set_get_and_invalid():
    from neat.activations import ActivationFunctionSet, InvalidActivationFunction
    s = ActivationFunctionSet()
    f = s.get('sigmoid')
    assert callable(f)
    assert s.is_valid('sigmoid') is True
    assert s.is_valid('definitely_not_a_function') is False
    with pytest.raises(InvalidActivationFunction):
        s.get('definitely_not_a_function')

def test_aggregation_basic():
    from neat.aggregations import (
        sum_aggregation, product_aggregation, max_aggregation,
        min_aggregation, maxabs_aggregation, mean_aggregation,
        median_aggregation,
    )
    data = [1.0, 2.0, 3.0, 4.0]
    assert sum_aggregation(data) == pytest.approx(10.0)
    assert product_aggregation(data) == pytest.approx(24.0)
    assert max_aggregation(data) == pytest.approx(4.0)
    assert min_aggregation(data) == pytest.approx(1.0)
    assert mean_aggregation(data) == pytest.approx(2.5)
    assert median_aggregation([1.0, 2.0, 3.0]) == pytest.approx(2.0)
    # maxabs picks element with largest absolute value (keeping sign)
    assert maxabs_aggregation([-5.0, 1.0, 2.0]) == pytest.approx(-5.0)

def test_aggregation_product_identity():
    from neat.aggregations import product_aggregation
    # single element product must equal that element (identity 1.0 fold)
    assert product_aggregation([7.0]) == pytest.approx(7.0)
    assert product_aggregation([2.0, 0.5]) == pytest.approx(1.0)

def test_aggregation_empty_returns_zero():
    from neat.aggregations import (
        sum_aggregation, max_aggregation, min_aggregation,
        mean_aggregation, median_aggregation, maxabs_aggregation,
    )
    for f in (sum_aggregation, max_aggregation, min_aggregation,
              mean_aggregation, median_aggregation, maxabs_aggregation):
        assert f([]) == pytest.approx(0.0)

def test_aggregation_set_get_invalid():
    from neat.aggregations import AggregationFunctionSet, InvalidAggregationFunction
    s = AggregationFunctionSet()
    assert callable(s.get('sum'))
    assert s.is_valid('sum') is True
    assert s.is_valid('nope_not_here') is False
    with pytest.raises(InvalidAggregationFunction):
        s.get('nope_not_here')

def test_float_attribute_clamp():
    from neat.attributes import FloatAttribute
    a = FloatAttribute('x')
    cfg = type('C', (), _float_config())()
    assert a.clamp(100.0, cfg) == pytest.approx(30.0)
    assert a.clamp(-100.0, cfg) == pytest.approx(-30.0)
    assert a.clamp(5.0, cfg) == pytest.approx(5.0)

def test_float_attribute_zero_rate_never_changes():
    from neat.attributes import FloatAttribute
    a = FloatAttribute('x')
    cfg = type('C', (), _float_config(x_mutate_rate=0.0, x_replace_rate=0.0))()
    v = 3.5
    for _ in range(50):
        assert a.mutate_value(v, cfg) == pytest.approx(v)

def test_float_attribute_validate_bad_range():
    from neat.attributes import FloatAttribute
    a = FloatAttribute('x')
    cfg = type('C', (), _float_config(x_max_value=-10.0, x_min_value=10.0))()
    with pytest.raises(RuntimeError):
        a.validate(cfg)

def test_float_attribute_bad_init_type():
    from neat.attributes import FloatAttribute
    a = FloatAttribute('x')
    cfg = type('C', (), _float_config(x_init_type='bogus'))()
    with pytest.raises(RuntimeError):
        a.init_value(cfg)

def test_bool_attribute_init_and_validate():
    from neat.attributes import BoolAttribute
    a = BoolAttribute('b')
    cfg = type('C', (), {
        'b_default': 'true', 'b_mutate_rate': 0.0,
        'b_rate_to_true_add': 0.0, 'b_rate_to_false_add': 0.0,
    })()
    assert a.init_value(cfg) is True
    bad = type('C', (), {
        'b_default': 'not_a_bool', 'b_mutate_rate': 0.0,
        'b_rate_to_true_add': 0.0, 'b_rate_to_false_add': 0.0,
    })()
    with pytest.raises(RuntimeError):
        a.validate(bad)

def test_bool_attribute_zero_rate_stable():
    from neat.attributes import BoolAttribute
    a = BoolAttribute('b')
    cfg = type('C', (), {
        'b_default': 'true', 'b_mutate_rate': 0.0,
        'b_rate_to_true_add': 0.0, 'b_rate_to_false_add': 0.0,
    })()
    for _ in range(50):
        assert a.mutate_value(True, cfg) is True

def test_string_attribute_validate_rejects_bad_default():
    from neat.attributes import StringAttribute
    a = StringAttribute('s')
    cfg = type('C', (), {
        's_default': 'notpresent', 's_options': ['a', 'b', 'c'],
        's_mutate_rate': 0.0,
    })()
    with pytest.raises(RuntimeError):
        a.validate(cfg)

def test_string_attribute_default_init():
    from neat.attributes import StringAttribute
    a = StringAttribute('s')
    cfg = type('C', (), {
        's_default': 'b', 's_options': ['a', 'b', 'c'],
        's_mutate_rate': 0.0,
    })()
    assert a.init_value(cfg) == 'b'

def test_attribute_config_items_not_shared():
    # Two attribute instances must not share the same mutable config-items list.
    from neat.attributes import FloatAttribute
    a = FloatAttribute('alpha')
    b = FloatAttribute('beta')
    pa = a.get_config_params()
    pb = b.get_config_params()
    names_a = {p.name for p in pa}
    names_b = {p.name for p in pb}
    # config param names are derived from the attribute name -> disjoint prefixes
    assert any(n.startswith('alpha_') for n in names_a)
    assert any(n.startswith('beta_') for n in names_b)
    assert not (names_a & names_b)
