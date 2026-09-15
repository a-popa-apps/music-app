from app.email_templates import (
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


def test_templates_produce_distinct_content():
    link = "https://crateprep.app/auth/action?oobCode=same"
    assert verification_email_html(link) != password_reset_email_html(link)
