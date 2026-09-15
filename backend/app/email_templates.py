from __future__ import annotations

import html

# Colors pulled directly from the frontend's own design tokens
# (frontend/src/index.css) so these emails actually look like CratePrep
# rather than a generic transactional-email template.
_ACCENT = "#ff6b35"
_ACCENT_2 = "#ff3d78"
_BG = "#000000"
_CARD_BG = "#17171a"
_BORDER = "rgba(255,255,255,0.1)"
_TEXT = "#ffffff"
_TEXT_MUTED = "rgba(255,255,255,0.7)"


def _base_email(preheader: str, heading: str, body_html: str, button_text: str, button_url: str) -> str:
    return f"""\
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  </head>
  <body style="margin:0; padding:0; background:{_BG}; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
    <div style="display:none; max-height:0; overflow:hidden; opacity:0;">{preheader}</div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_BG};">
      <tr>
        <td align="center" style="padding:40px 16px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;">
            <tr>
              <td style="padding-bottom:28px;">
                <span style="font-family:ui-monospace,'JetBrains Mono',monospace; font-weight:700; font-size:18px; letter-spacing:-0.02em; color:{_TEXT};">crateprep.</span>
              </td>
            </tr>
            <tr>
              <td style="background:{_CARD_BG}; border:1px solid {_BORDER}; border-radius:16px; padding:36px 32px;">
                <h1 style="margin:0 0 16px; font-size:22px; line-height:1.3; color:{_TEXT};">{heading}</h1>
                <div style="font-size:15px; line-height:1.6; color:{_TEXT_MUTED};">
                  {body_html}
                </div>
                <table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:28px;">
                  <tr>
                    <td style="border-radius:999px; background:linear-gradient(90deg,{_ACCENT},{_ACCENT_2});">
                      <a href="{button_url}" style="display:inline-block; padding:14px 28px; font-size:15px; font-weight:600; color:#ffffff; text-decoration:none; border-radius:999px;">{button_text}</a>
                    </td>
                  </tr>
                </table>
                <p style="margin:24px 0 0; font-size:12.5px; line-height:1.6; color:rgba(255,255,255,0.4); word-break:break-all;">
                  Or paste this link into your browser:<br />
                  <a href="{button_url}" style="color:{_ACCENT}; text-decoration:none;">{button_url}</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding-top:24px; font-size:12.5px; color:rgba(255,255,255,0.35); text-align:center;">
                CratePrep &middot; Surgical track organization for precision DJs
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def verification_email_html(action_link: str) -> str:
    return _base_email(
        preheader="Confirm your email to start using CratePrep.",
        heading="Confirm your email",
        body_html=(
            "One click and you're in — verifying your email unlocks your "
            "10 free tracks a month, saved history, and drag-to-reorder."
        ),
        button_text="Verify Email",
        button_url=action_link,
    )


def welcome_email_html(app_url: str) -> str:
    return _base_email(
        preheader="Your email is verified -- you're ready to organize your crate.",
        heading="Welcome to CratePrep",
        body_html=(
            "You're verified and ready to go. Drop in a batch of tracks and "
            "CratePrep will clean up filenames, tag genres, and get your "
            "crate DJ-ready in minutes -- 10 tracks a month free, no card "
            "required."
        ),
        button_text="Start Organizing",
        button_url=app_url,
    )


def subscription_started_email_html(trial_days: int | None, manage_billing_url: str) -> str:
    if trial_days:
        body_html = (
            f"Your {trial_days}-day free trial of CratePrep Pro has started -- "
            "unlimited tracks, AI set ordering, and saved templates are all "
            "unlocked right now. You won't be charged until the trial ends, "
            "and you can cancel anytime before then."
        )
    else:
        body_html = (
            "You're all set. Unlimited tracks, AI set ordering, and saved "
            "templates are unlocked on your account."
        )
    return _base_email(
        preheader="Your CratePrep Pro subscription is active.",
        heading="Welcome to CratePrep Pro",
        body_html=body_html,
        button_text="Manage Billing",
        button_url=manage_billing_url,
    )


def subscription_canceled_email_html(resubscribe_url: str) -> str:
    return _base_email(
        preheader="Your CratePrep Pro subscription has ended.",
        heading="Subscription canceled",
        body_html=(
            "Your CratePrep Pro subscription has ended, and your account is "
            "now on the Free plan (10 tracks a month). Your saved templates "
            "and history are still there if you resubscribe."
        ),
        button_text="Resubscribe",
        button_url=resubscribe_url,
    )


def usage_limit_warning_email_html(tracks_used: int, tracks_limit: int, upgrade_url: str) -> str:
    return _base_email(
        preheader=f"You've used {tracks_used} of {tracks_limit} free tracks this month.",
        heading="Almost at your monthly limit",
        body_html=(
            f"You've processed {tracks_used} of your {tracks_limit} free "
            "tracks this month. Upgrade to Pro for unlimited tracks, AI set "
            "ordering, and saved templates -- or your limit resets at the "
            "start of next month."
        ),
        button_text="Upgrade to Pro",
        button_url=upgrade_url,
    )


def password_changed_email_html(reset_url: str) -> str:
    return _base_email(
        preheader="Your CratePrep password was just changed.",
        heading="Your password was changed",
        body_html=(
            "This confirms your CratePrep account password was just "
            "changed. If this was you, no action is needed. If you didn't "
            "make this change, secure your account immediately by "
            "resetting your password again."
        ),
        button_text="Reset Password",
        button_url=reset_url,
    )


def ai_limit_alert_email_html(heading: str, detail: str, admin_url: str) -> str:
    return _base_email(
        preheader=heading,
        heading=heading,
        body_html=detail,
        button_text="View Admin Dashboard",
        button_url=admin_url,
    )


def payment_failed_email_html(manage_billing_url: str) -> str:
    return _base_email(
        preheader="We couldn't process your CratePrep Pro payment.",
        heading="We couldn't process your payment",
        body_html=(
            "Your card was declined on your CratePrep Pro subscription. "
            "Update your payment method to keep your unlimited tracks, AI "
            "set ordering, and saved templates — your account will "
            "revert to the Free plan if this isn't resolved."
        ),
        button_text="Update Payment Method",
        button_url=manage_billing_url,
    )


def new_feedback_email_html(
    category: str,
    subject: str | None,
    message: str,
    submitter_email: str | None,
    admin_url: str,
) -> str:
    # subject/message/submitter_email are user-submitted -- escape before
    # embedding, same reason any other app would escape untrusted input
    # into HTML. An email client is a lower-severity target than a browser,
    # but there's no reason to skip it: a submission is free-form text a
    # stranger controls, up to and including a fake "unsubscribe" link or
    # markup that breaks the layout.
    label = "support request" if category == "support" else "feedback"
    lines = [f"<strong>From:</strong> {html.escape(submitter_email) if submitter_email else 'anonymous'}"]
    if subject:
        lines.append(f"<strong>Subject:</strong> {html.escape(subject)}")
    escaped_message = html.escape(message).replace("\n", "<br />")
    lines.append(f"<br />{escaped_message}")

    return _base_email(
        preheader=f"New {label} submitted on CratePrep.",
        heading=f"New {label}",
        body_html="<br />".join(lines),
        button_text="View in Admin",
        button_url=admin_url,
    )


def password_reset_email_html(action_link: str) -> str:
    return _base_email(
        preheader="Reset your CratePrep password.",
        heading="Reset your password",
        body_html=(
            "Someone (hopefully you) asked to reset the password on this "
            "account. Click below to choose a new one — this link expires "
            "soon and can only be used once. If you didn't request this, "
            "you can safely ignore this email."
        ),
        button_text="Reset Password",
        button_url=action_link,
    )
