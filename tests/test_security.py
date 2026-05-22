"""Tests for security utilities."""


from app.utils.security import (
    DESTRUCTIVE_TOOLS,
    check_sql_injection,
    check_xss,
    sanitize_input,
    validate_chat_input,
)


class TestSanitizeInput:
    def test_removes_null_bytes(self) -> None:
        assert sanitize_input("hello\x00world") == "helloworld"

    def test_strips_control_chars(self) -> None:
        assert sanitize_input("hello\x01world") == "helloworld"

    def test_preserves_newlines_and_tabs(self) -> None:
        assert sanitize_input("hello\nworld\ttab") == "hello\nworld\ttab"

    def test_strips_leading_trailing_whitespace(self) -> None:
        assert sanitize_input("  hello  ") == "hello"


class TestCheckSQLInjection:
    def test_detects_select(self) -> None:
        assert check_sql_injection("SELECT * FROM users") is True

    def test_detects_union(self) -> None:
        assert check_sql_injection("' UNION SELECT") is True

    def test_detects_or_equals(self) -> None:
        assert check_sql_injection("' OR 1=1 --") is True

    def test_safe_input(self) -> None:
        assert check_sql_injection("Hello, how are you?") is False


class TestCheckXSS:
    def test_detects_script_tag(self) -> None:
        assert check_xss("<script>alert('xss')</script>") is True

    def test_detects_javascript_protocol(self) -> None:
        assert check_xss("javascript:alert(1)") is True

    def test_detects_onload(self) -> None:
        assert check_xss("<img src=x onerror=alert(1)>") is True

    def test_safe_input(self) -> None:
        assert check_xss("Hello world") is False


class TestValidateChatInput:
    def test_safe_message(self) -> None:
        result = validate_chat_input("Hello, Kodee!")
        assert result["safe"] is True
        assert result["issues"] == []
        assert result["sanitized"] == "Hello, Kodee!"

    def test_sql_injection_detected(self) -> None:
        result = validate_chat_input("DROP TABLE users")
        assert result["safe"] is False
        assert "sql_injection" in result["issues"]

    def test_xss_detected(self) -> None:
        result = validate_chat_input("<script>alert(1)</script>")
        assert result["safe"] is False
        assert "xss" in result["issues"]

    def test_multiple_issues(self) -> None:
        result = validate_chat_input("<script>SELECT * FROM users</script>")
        assert result["safe"] is False
        assert len(result["issues"]) == 2


class TestDestructiveTools:
    def test_contains_delete_record(self) -> None:
        assert "delete_record" in DESTRUCTIVE_TOOLS

    def test_contains_restore_backup(self) -> None:
        assert "restore_backup" in DESTRUCTIVE_TOOLS
