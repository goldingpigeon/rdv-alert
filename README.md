# rdv-alert

Emails you when appointments open at the Algerian Consulate in Montreal
(every service except VISA: biometric passport, passport on Saturday, national ID card).

Checks **every minute**, around the clock, with GitHub Actions. Each run monitors for
about 5h40m and then starts the next one itself; a schedule restarts it if the chain ever breaks.

Only appointments between **DATE_FROM** and **DATE_TO** trigger an alert (default
2026-11-15 to 2026-12-10). To change the dates, add repository *variables* `DATE_FROM` /
`DATE_TO` (format `YYYY-MM-DD`) in **Settings → Secrets and variables → Actions → Variables**.

## Setup

In **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
|---|---|
| `SMTP_USER` | Gmail address that sends the alerts |
| `SMTP_PASS` | Gmail app password for that address |
| `EMAIL_TO` | Recipients, comma-separated |

## Testing

**Actions → Check consulate appointments → Run workflow**. With no box ticked it starts the
monitor right away. Tick one box for a quick test:

- **Send a test email**: checks that email sending works.
- **SIMULATION**: sends a full alert email with fake passport slots (subject starts with 🧪 SIMULATION). Nothing is saved, real alerts are not affected.
- **TEST: also watch VISA**: sends a real alert using VISA's real open slots, with its own memory.

## Notes

- You get one email per new opening, not one every minute.
- To stop monitoring: cancel the running run in the Actions tab (it won't start another;
  the schedule restarts it within ~15 min unless you also disable the workflow).
- GitHub pauses scheduled workflows after 60 days with no repo activity. The **Keepalive**
  workflow makes an empty commit on the 1st of each month to prevent that. If alerts ever stop,
  open the Actions tab and re-enable the workflow.
