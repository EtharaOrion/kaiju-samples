import gc
import weakref
import enum

import pytest

from transitions.core import (
    Machine,
    State,
    Transition,
    Event,
    EventData,
    Condition,
    MachineError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class Stuff(object):
    def __init__(self):
        self.calls = []
        self.flag = False

    def record(self, *args, **kwargs):
        self.calls.append(("record", args, kwargs))

    def set_flag_true(self):
        self.flag = True

    def is_flag_true(self):
        return self.flag

    def is_flag_false(self):
        return not self.flag


# ---------------------------------------------------------------------------
# Basic transitions
# ---------------------------------------------------------------------------









# ---------------------------------------------------------------------------
# State name / value semantics
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Conditions and unless (target polarity)
# ---------------------------------------------------------------------------









# ---------------------------------------------------------------------------
# Internal transitions (dest is None)
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# send_event dispatch
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Callback ordering: prepare -> before -> on_exit -> on_enter -> after
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Auto-transitions
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# may_ guards
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Short-circuit: first successful transition wins
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Error / finalize routing
# ---------------------------------------------------------------------------









# ---------------------------------------------------------------------------
# Model lifecycle & garbage collection
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Machine as its own model
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Ordered transitions
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# get_state / set_state
# ---------------------------------------------------------------------------







# ---------------------------------------------------------------------------
# resolve_callable
# ---------------------------------------------------------------------------


def test_basic_transition_changes_state():
    m = Machine(states=["A", "B", "C"], initial="A")
    m.add_transition("go", "A", "B")
    assert m.state == "A"
    assert m.go() is True
    assert m.state == "B"

def test_trigger_returns_boolean():
    m = Machine(states=["A", "B"], initial="A")
    m.add_transition("go", "A", "B")
    result = m.go()
    assert result is True
    assert isinstance(result, bool)

def test_invalid_source_raises_machine_error():
    m = Machine(states=["A", "B"], initial="A")
    m.add_transition("go", "B", "A")  # only valid from B
    with pytest.raises(MachineError):
        m.go()
    # state unchanged
    assert m.state == "A"

def test_ignore_invalid_triggers_returns_false():
    m = Machine(states=["A", "B"], initial="A", ignore_invalid_triggers=True)
    m.add_transition("go", "B", "A")
    assert m.go() is False
    assert m.state == "A"

def test_state_name_and_value_for_string():
    s = State("hello")
    assert s.name == "hello"
    assert s.value == "hello"

def test_enum_state_name_and_value():
    class Color(enum.Enum):
        RED = 1
        GREEN = 2

    m = Machine(states=Color, initial=Color.RED)
    # model state stores the enum member value
    assert m.state == Color.RED
    state_obj = m.get_state(Color.RED)
    assert state_obj.name == "RED"
    assert state_obj.value == Color.RED

def test_condition_gates_transition():
    s = Stuff()
    m = Machine(model=s, states=["A", "B"], initial="A")
    m.add_transition("go", "A", "B", conditions="is_flag_true")
    # flag false -> blocked
    assert s.go() is False
    assert s.state == "A"
    s.flag = True
    assert s.go() is True
    assert s.state == "B"

def test_unless_uses_target_false():
    s = Stuff()
    m = Machine(model=s, states=["A", "B"], initial="A")
    m.add_transition("go", "A", "B", unless="is_flag_true")
    # flag false -> unless satisfied -> allowed
    assert s.go() is True
    assert s.state == "B"

def test_unless_blocks_when_true():
    s = Stuff()
    m = Machine(model=s, states=["A", "B"], initial="A")
    s.flag = True
    m.add_transition("go", "A", "B", unless="is_flag_true")
    assert s.go() is False
    assert s.state == "A"

def test_condition_check_directly():
    c_true = Condition("is_flag_true", target=True)
    c_false = Condition("is_flag_true", target=False)
    s = Stuff()
    m = Machine(model=s, states=["A"], initial="A")
    # Build EventData for the model
    ev = EventData(m.get_state("A"), Event("dummy", m), m, s, args=(), kwargs={})
    s.flag = True
    assert c_true.check(ev) is True
    assert c_false.check(ev) is False
    s.flag = False
    assert c_true.check(ev) is False
    assert c_false.check(ev) is True

def test_internal_transition_does_not_change_state():
    counter = {"n": 0}

    def cb():
        counter["n"] += 1

    m = Machine(states=["A", "B"], initial="A")
    m.add_transition("tick", "A", dest=None, after=cb)
    assert m.state == "A"
    assert m.tick() is True
    # state unchanged for internal transition
    assert m.state == "A"
    assert counter["n"] == 1

def test_send_event_passes_event_data():
    seen = {}

    class Model(object):
        def cond(self, event):
            seen["type"] = type(event).__name__
            seen["extra"] = event.kwargs.get("extra")
            return True

    model = Model()
    m = Machine(model=model, states=["A", "B"], initial="A", send_event=True)
    m.add_transition("go", "A", "B", conditions="cond")
    assert model.go(extra=42) is True
    assert seen["type"] == "EventData"
    assert seen["extra"] == 42

def test_no_send_event_unpacks_args():
    seen = {}

    class Model(object):
        def cond(self, x=None):
            seen["x"] = x
            return True

    model = Model()
    m = Machine(model=model, states=["A", "B"], initial="A", send_event=False)
    m.add_transition("go", "A", "B", conditions="cond")
    assert model.go(x=7) is True
    assert seen["x"] == 7

def test_callback_ordering():
    order = []

    class Model(object):
        def prep(self):
            order.append("prepare")

        def bef(self):
            order.append("before")

        def aft(self):
            order.append("after")

        def on_exit_A(self):
            order.append("exit_A")

        def on_enter_B(self):
            order.append("enter_B")

    model = Model()
    m = Machine(model=model, states=["A", "B"], initial="A")
    m.add_transition("go", "A", "B", prepare="prep", before="bef", after="aft")
    model.go()
    assert order.index("prepare") < order.index("before")
    assert order.index("before") < order.index("exit_A")
    assert order.index("exit_A") < order.index("enter_B")
    assert order.index("enter_B") < order.index("after")

def test_auto_transitions_generated():
    m = Machine(states=["A", "B", "C"], initial="A")
    assert hasattr(m.model, "to_B")
    assert m.to_B() is True
    assert m.state == "B"
    assert m.to_C() is True
    assert m.state == "C"

def test_auto_transitions_can_be_disabled():
    m = Machine(states=["A", "B"], initial="A", auto_transitions=False)
    assert not hasattr(m.model, "to_B")

def test_may_transition_reports_feasibility():
    m = Machine(states=["A", "B", "C"], initial="A")
    m.add_transition("go", "A", "B")
    assert m.may_go() is True
    m.to_C()
    # from C, 'go' is not valid
    assert m.may_go() is False

def test_first_successful_transition_wins():
    s = Stuff()
    m = Machine(model=s, states=["A", "B", "C"], initial="A")
    # two transitions for the same trigger; first is gated off
    m.add_transition("go", "A", "B", conditions="is_flag_true")
    m.add_transition("go", "A", "C")
    # flag false: first blocked, second taken -> C
    assert s.go() is True
    assert s.state == "C"

def test_short_circuit_stops_at_first_true():
    s = Stuff()
    m = Machine(model=s, states=["A", "B", "C"], initial="A")
    m.add_transition("go", "A", "B")  # this fires first
    m.add_transition("go", "A", "C")
    assert s.go() is True
    assert s.state == "B"  # must stop at B, not proceed to C

def test_on_exception_routes_when_configured():
    handled = {}

    def boom():
        raise ValueError("boom")

    def handler(event_data):
        handled["err"] = str(event_data.error)

    m = Machine(states=["A", "B"], initial="A", send_event=True)
    m.on_exception.append(handler)
    m.add_transition("go", "A", "B", before=boom)
    # should not raise since on_exception is configured
    m.go()
    assert "boom" in handled["err"]

def test_exception_propagates_without_handler():
    def boom():
        raise ValueError("kaboom")

    m = Machine(states=["A", "B"], initial="A")
    m.add_transition("go", "A", "B", before=boom)
    with pytest.raises(ValueError):
        m.go()

def test_finalize_event_always_runs():
    calls = {"n": 0}

    def finalize(event_data):
        calls["n"] += 1

    m = Machine(states=["A", "B"], initial="A", send_event=True,
                finalize_event=[finalize])
    m.add_transition("go", "A", "B")
    m.go()
    assert calls["n"] == 1

def test_add_and_remove_model():
    m = Machine(states=["A", "B"], initial="A")
    model = Stuff()
    m.add_model(model)
    assert model.state == "A"
    m.add_transition("go", "A", "B")
    assert model.go() is True
    assert model.state == "B"
    m.remove_model(model)

def test_removed_model_is_garbage_collectable():
    m = Machine(states=["A", "B"], initial="A")
    model = Stuff()
    m.add_model(model)
    ref = weakref.ref(model)
    m.remove_model(model)
    del model
    gc.collect()
    assert ref() is None

def test_machine_is_own_model_by_default():
    m = Machine(states=["A", "B"], initial="A")
    m.add_transition("go", "A", "B")
    # trigger method exists directly on machine
    assert m.go() is True
    assert m.state == "B"

def test_ordered_transitions():
    m = Machine(states=["A", "B", "C"], initial="A")
    m.add_ordered_transitions()
    assert m.state == "A"
    m.next_state()
    assert m.state == "B"
    m.next_state()
    assert m.state == "C"
    m.next_state()
    assert m.state == "A"  # wraps around

def test_get_state_returns_state_object():
    m = Machine(states=["A", "B"], initial="A")
    st = m.get_state("A")
    assert isinstance(st, State)
    assert st.name == "A"

def test_get_state_invalid_raises():
    m = Machine(states=["A", "B"], initial="A")
    with pytest.raises(ValueError):
        m.get_state("nonexistent")

def test_set_state_changes_current():
    m = Machine(states=["A", "B"], initial="A")
    m.set_state("B")
    assert m.state == "B"

def test_resolve_callable_binds_string_to_model_method():
    s = Stuff()
    m = Machine(model=s, states=["A"], initial="A")
    ev = EventData(m.get_state("A"), Event("d", m), m, s, args=(), kwargs={})
    func = m.resolve_callable("is_flag_false", ev)
    assert callable(func)
    assert func() is True

def test_resolve_callable_passes_through_actual_callable():
    m = Machine(states=["A"], initial="A")
    fn = lambda: 99
    ev = EventData(m.get_state("A"), Event("d", m), m, m, args=(), kwargs={})
    resolved = m.resolve_callable(fn, ev)
    assert resolved() == 99
