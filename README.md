# rdv-alert

Emails you when appointments open at the Algerian Consulate in Montreal
(every service except VISA: biometric passport, passport on Saturday, national ID card).

Runs automatically every 5 minutes with GitHub Actions.

## Setup

In **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
|---|---|
| `SMTP_USER` | Gmail address that sends the alerts |
| `SMTP_PASS` | Gmail app password for that address |
| `EMAIL_TO` | Recipients, comma-separated |

## Testing

**Actions → Check consulate appointments → Run workflow**, then tick one box:

- **Send a test email**: checks that email sending works.
- **SIMULATION**: sends a full alert email with fake passport slots (subject starts with 🧪 SIMULATION). Nothing is saved, real alerts are not affected.
- **TEST: also watch VISA**: sends a real alert using VISA's real open slots, with its own memory.

## Notes

- You get one email per new opening, not one every 5 minutes.
- GitHub pauses scheduled workflows after 60 days with no repo activity. The **Keepalive**
  workflow makes an empty commit on the 1st of each month to prevent that. If alerts ever stop,
  open the Actions tab and re-enable the workflow.
