"""Placeholder test to verify pytest is working."""


def test_placeholder() -> None:
    """Verify test infrastructure works."""
    assert True, "Test infrastructure is working"


def test_import_meta() -> None:
    """Verify meta package can be imported."""
    import meta  # noqa: F401

    assert meta is not None


def test_import_apps() -> None:
    """Verify apps package can be imported."""
    import apps  # noqa: F401

    assert apps is not None
