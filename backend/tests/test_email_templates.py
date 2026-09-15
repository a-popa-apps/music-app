from app.email_templates import (
    new_feedback_email_html,
    password_reset_email_html,
    payment_failed_email_html,
    verification_email_html,
)


def test_verification_email_embeds_the_action_link():
    html = verification_email_html("https://crateprep.app/auth/action?mode=verifyEmail&oobCode=abc")
    assert "https://crateprep.app/auth/action?mode=verifyEmail&oobCode=abc" in html
    assert "Verify Email" in html
    assert "crateprep." in html


def test_password_reset_email_embeds_the_action_link():
    html = password_reset_email_html("https://crateprep.app/auth/action?mode=resetPassword&oobCode=xyz")
    assert "https://crateprep.app/auth/action?mode=resetPassword&oobCode=xyz" in html
    assert "Reset Password" in html
    assert "crateprep." in html


def test_payment_failed_email_embeds_the_manage_billing_link():
    html = payment_failed_email_html("https://crateprep.app/profile")
    assert "https://crateprep.app/profile" in html
    assert "Update Payment Method" in html
    assert "crateprep." in html


def test_new_feedback_email_embeds_the_admin_link_and_content():
    html = new_feedback_email_html(
        "support", "Login broken", "It just spins", "user@example.com", "https://crateprep.app/admin"
    )
    assert "https://crateprep.app/admin" in html
    assert "View in Admin" in html
    assert "user@example.com" in html
    assert "Login broken" in html
    assert "It just spins" in html
    assert "support request" in html


def test_new_feedback_email_escapes_user_submitted_content():
    html = new_feedback_email_html(
        "feedback",
        "<script>alert(1)</script>",
        "hello & <b>world</b>",
        "\"><img src=x>@example.com",
        "https://crateprep.app/admin",
    )
    assert "<script>" not in html
    assert "<img src=x>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp;" in html


def test_new_feedback_email_shows_anonymous_when_no_email_given():
    html = new_feedback_email_html("feedback", None, "hi", None, "https://crateprep.app/admin")
    assert "anonymous" in html


def test_templates_produce_distinct_content():
    link = "https://crateprep.app/auth/action?oobCode=same"
    assert verification_email_html(link) != password_reset_email_html(link)
