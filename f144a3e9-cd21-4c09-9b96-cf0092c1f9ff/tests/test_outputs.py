from btclib.alias import *
import pytest


def test_differential_0():
    assert repr(str(Point)) == "'typing.Tuple[int, int]'"

def test_differential_1():
    assert repr(str(JacPoint)) == "'typing.Tuple[int, int, int]'"

def test_differential_2():
    assert repr(str(Octets)) == "'typing.Union[bytes, str]'"

def test_differential_3():
    assert repr(str(String)) == "'typing.Union[bytes, str]'"

def test_differential_4():
    assert repr(str(Integer)) == "'typing.Union[bytes, str, int]'"

def test_differential_5():
    assert repr(str(BinaryData)) == "'typing.Union[_io.BytesIO, bytes, str]'"

def test_differential_6():
    assert repr(isinstance((1, 2), tuple)) == 'True'

def test_differential_7():
    assert repr(repr(Point)) == "'typing.Tuple[int, int]'"

def test_differential_8():
    assert repr(callable(Point)) == 'True'

def test_differential_9():
    assert repr(hasattr(Point, '__args__')) == 'True'

def test_differential_10():
    assert repr(str(Command)) == "'typing.Union[int, str, bytes]'"

def test_differential_11():
    assert repr(str(ScriptList)) == "'typing.List[typing.Union[int, str, bytes]]'"

def test_differential_12():
    assert repr(isinstance(b'\x00', bytes)) == 'True'

def test_differential_13():
    assert repr(str(HashF)) == "'typing.Callable[[], typing.Any]'"



# ---- LLM-authored (golden-validated) tests ----
import importlib
import hashlib
from decimal import Decimal

import pytest


# ---------------------------------------------------------------------------
# Robust importer: the btclib modules may be importable either as a package
# (``btclib.foo``) or with the package root on sys.path (``foo``).
# ---------------------------------------------------------------------------
def _imp(name):
    last = None
    for full in (f"btclib.{name}", name):
        try:
            return importlib.import_module(full)
        except Exception as e:  # noqa: BLE001
            last = e
            continue
    raise last


base58 = _imp("base58")
utils = _imp("utils")
amount_mod = _imp("amount")
hashes = _imp("hashes")
var_int = _imp("var_int")
number_theory = _imp("number_theory")
curve_mod = _imp("ec.curve")
bip39 = _imp("mnemonic.bip39")
exceptions = _imp("exceptions")

BTClibValueError = getattr(exceptions, "BTClibValueError", ValueError)


# ---------------------------------------------------------------------------
# base58 (base58check)
# ---------------------------------------------------------------------------






# ---------------------------------------------------------------------------
# utils.bytes_from_octets
# ---------------------------------------------------------------------------










# ---------------------------------------------------------------------------
# hashes: hash160 / hash256  (compared against hashlib reference)
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# amount conversions (Decimal, no float contamination)
# ---------------------------------------------------------------------------


def test_base58_known_burn_address():
    # version 0x00 + 20 zero bytes  ->  the well known "1" burn address
    payload = bytes(21)
    encoded = base58.b58encode(payload)
    assert isinstance(encoded, (str, bytes))
    if isinstance(encoded, bytes):
        encoded = encoded.decode("ascii")
    assert encoded == "1111111111111111111114oLvT2"

def test_base58_round_trip_and_checksum():
    for payload in (bytes(21), b"\x00\x01\x02\x03\x04", bytes(range(25))):
        enc = base58.b58encode(payload)
        dec = base58.b58decode(enc)
        assert bytes(dec) == payload

def test_base58_bad_checksum_rejected():
    good = base58.b58encode(bytes(21))
    if isinstance(good, bytes):
        good = good.decode("ascii")
    # corrupt a character -> checksum must fail
    bad = good[:-1] + ("A" if good[-1] != "A" else "B")
    with pytest.raises(Exception):
        base58.b58decode(bad)

def test_bytes_from_octets_hex_string():
    assert utils.bytes_from_octets("48656c6c6f") == b"Hello"

def test_bytes_from_octets_bytes_passthrough():
    assert utils.bytes_from_octets(b"Hello") == b"Hello"

def test_bytes_from_octets_accepts_embedded_spaces():
    assert utils.bytes_from_octets("48 65 6c 6c 6f") == b"Hello"

def test_bytes_from_octets_length_ok():
    assert utils.bytes_from_octets("0011", 2) == b"\x00\x11"

def test_bytes_from_octets_wrong_length_raises():
    with pytest.raises(BTClibValueError):
        utils.bytes_from_octets("0011", 3)

def test_hash256_matches_double_sha256():
    for data in (b"", b"abc", b"\x00" * 32):
        expected = hashlib.sha256(hashlib.sha256(data).digest()).digest()
        assert hashes.hash256(data) == expected

def test_hash160_matches_ripemd_of_sha256():
    try:
        hashlib.new("ripemd160")
    except Exception:
        pytest.skip("ripemd160 not available in hashlib")
    for data in (b"", b"abc", b"\x00" * 20):
        h = hashlib.new("ripemd160")
        h.update(hashlib.sha256(data).digest())
        expected = h.digest()
        assert hashes.hash160(data) == expected

def test_btc_from_sats():
    v = amount_mod.btc_from_sats(100_000_000)
    assert isinstance(v, Decimal)
    assert v == Decimal("1")
    assert amount_mod.btc_from_sats(1) == Decimal("0.00000001")
