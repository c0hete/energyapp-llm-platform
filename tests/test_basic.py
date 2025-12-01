def test_placeholder():
    """Sanity check: la suite de pruebas está funcionando."""
    assert True


if __name__ == "__main__":
    # Permite ejecutar este archivo directamente sin depender de pytest.
    try:
        import pytest  # type: ignore
        raise SystemExit(pytest.main([__file__]))
    except ModuleNotFoundError:
        print("pytest no está instalado; ejecuta: pip install pytest")
