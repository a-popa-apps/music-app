from app.email_templates import (
    new_feedback_email_html,
    password_changed_email_html,
    password_reset_email_html,
    payment_failed_email_html,
    subscription_canceled_email_html,
    subscription_started_email_html,
    usage_limit_warning_email_html,
    verification_email_html,
    welcome_email_html,
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


def test_welcome_email_embeds_the_app_link():
    html = welcome_email_html("https://crateprep.app/")
    assert "https://crateprep.app/" in html
    assert "Start Organizing" in html
    assert "Welcome to CratePrep" in html


def test_subscription_started_email_mentions_trial_when_trialing():
    html = subscription_started_email_html(7, "https://crateprep.app/profile")
    assert "7-day free trial" in html
    assert "won't be charged" in html
    assert "Manage Billing" in html
    assert "https://crateprep.app/profile" in html


def test_subscription_started_email_no_trial_mention_when_not_trialing():
    html = subscription_started_email_html(None, "https://crateprep.app/profile")
    assert "trial" not in html.lower()
    assert "Welcome to CratePrep Pro" in html


def test_subscription_canceled_email_embeds_resubscribe_link():
    html = subscription_canceled_email_html("https://crateprep.app/pricing")
    assert "https://crateprep.app/pricing" in html
    assert "Resubscribe" in html
    assert "Free plan" in html


def test_usage_limit_warning_email_shows_used_and_limit():
    html = usage_limit_warning_email_html(8, 10, "https://crateprep.app/pricing")
    assert "8 of your 10 free" in html
    assert "Upgrade to Pro" in html
    assert "https://crateprep.app/pricing" in html


def test_password_changed_email_embeds_reset_link():
    html = password_changed_email_html("https://crateprep.app/auth")
    assert "https://crateprep.app/auth" in html
    assert "Reset Password" in html
    assert "password was changed" in html.lower()


def test_templates_produce_distinct_content():
    link = "https://crateprep.app/auth/action?oobCode=same"
    assert verification_email_html(link) != password_reset_email_html(link)
