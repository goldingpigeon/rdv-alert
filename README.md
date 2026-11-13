# Consulate appointment alert (Algerian Consulate, Montreal)

Checks the consulate booking page every 5 minutes for open
**"Passeport Biométrique et Carte Nationale d'Identité"** appointments and
emails two addresses with the open times and the booking link.

The consulate posts new appointments on the **1st and 15th** of each month.

## Setup (about 10 minutes)

1. **Gmail app password** (for the account that *sends* the alert):
   - Turn on 2-Step Verification: https://myaccount.google.com/security
   - Create an app password: https://myaccount.google.com/apppasswords
   - Copy the 16-letter password.
2. **Create a new *Public* GitHub repository** and upload these files,
   including the `.github/workflows/check.yml` folder.
   Public matters: GitHub Actions is free and unlimited for public repos, while a
   private repo's free 2,000 minutes would run out in about a week at this pace.
   Your emails and password stay hidden because they go in Secrets, not in the code.
3. In the repo go to **Settings → Secrets and variables → Actions → New repository secret**, and add:
   | Name | Value |
   |---|---|
   | `SMTP_USER` | the Gmail address that sends the alert |
   | `SMTP_PASS` | the 16-letter app password |
   | `EMAIL_TO`  | both recipient emails, comma-separated: `first@gmail.com,second@gmail.com` |
4. Go to the **Actions** tab, enable workflows, open **Check consulate appointments**
   and click **Run workflow** to test it.

## Options
- Also watch the Saturday passport service: add a secret-free env var in the
  workflow, `SERVICE_MATCH: "passeport"` (matches every passport service).
- Test locally without sending email:
  `DRY_RUN=1 python3 check_slots.py`

## Good to know
- GitHub pauses scheduled workflows after 60 days with no commits to the repo. If alerts stop,
  open the Actions tab and re-enable it (GitHub also emails you before that happens).
