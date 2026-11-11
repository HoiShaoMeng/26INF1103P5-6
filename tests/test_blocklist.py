"""Unit tests for Blocklist: which entry blocks a sender, and that public mail domains are never blocked whole."""

import os
import sys

import pytest

# adds the src/domain folder to the path so we can import blocklist.py for testing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "domain"))

from blocklist import Blocklist  # type: ignore


@pytest.mark.parametrize("sender, entry", [
    ("ceo@evil.com", "evil.com"),
    ("  CEO@Evil.COM ", "evil.com"),
    ("bob@gmail.com", "bob@gmail.com"),
    ("not-an-email", ""),
    ("bob@", ""),
    (None, ""),
])
def test_entry_for_blocks_company_domains_and_exact_public_addresses(sender, entry):
    assert Blocklist.entry_for(sender) == entry


def test_blocking_a_company_domain_blocks_every_sender_from_it():
    blocklist = Blocklist()
    assert blocklist.block_sender("ceo@evil.com") == "evil.com"
    assert blocklist.contains_sender("hr@evil.com") is True
    assert blocklist.contains_sender("hr@good.com") is False


def test_blocking_a_public_address_does_not_block_other_users():
    blocklist = Blocklist()
    blocklist.block_sender("scammer@gmail.com")
    assert blocklist.contains_sender("scammer@gmail.com") is True
    assert blocklist.contains_sender("friend@gmail.com") is False


def test_invalid_sender_is_never_blocked():
    blocklist = Blocklist()
    assert blocklist.block_sender("not-an-email") == ""
    assert len(blocklist) == 0
    assert blocklist.contains_sender("not-an-email") is False


def test_entries_are_normalised_unique_and_sorted():
    blocklist = Blocklist(["Evil.com", "evil.com", "  b.com ", "", None, 5])
    assert blocklist.entries == ["b.com", "evil.com"]


def test_entries_property_returns_a_copy():
    blocklist = Blocklist(["evil.com"])
    blocklist.entries.append("other.com")
    assert blocklist.entries == ["evil.com"]
