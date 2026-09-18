

def test_validate_config_survives_a_key_with_no_type_contract():
    """Regression: `rad doctor` crashed on any boolean setting missing from CONFIG_TYPES
    (`bool not in None`), which is exactly how a newly added config key gets deployed."""
    from rad.home import DEFAULTS
    from rad.storage import CONFIG_TYPES, validate_config

    assert validate_config({"not_a_real_key": True})[0].key == "not_a_real_key"
    issues = validate_config({"some_untyped_flag": True})
    assert [i.key for i in issues] == ["some_untyped_flag"]          # unknown → reported, no crash
    assert validate_config({"auto": "yes"})[0].problem.startswith("expected")
    assert validate_config({"max_tool_rounds": 999})[0].problem.startswith("out of range")
    # every real setting has a declared type, so a new one cannot slip through unvalidated
    assert set(DEFAULTS) == set(CONFIG_TYPES)
