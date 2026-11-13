#!/usr/bin/env python3
"""Check the Algerian Consulate (Montreal) booking page for open
"Passeport Biométrique et Carte Nationale d'Identité" appointments and
email an alert when new ones appear.

Settings come from environment variables:
  SMTP_USER   Gmail address that sends the alert
  SMTP_PASS   Gmail *app password* for that address
  EMAIL_TO    recipients, comma-separated (e.g. "a@x.com,b@y.com")
  SERVICE_MATCH  optional, comma-separated words a service title must contain
                 (default: "carte nationale")
  STATE_FILE  optional, where already-notified slots are remembered
  DRY_RUN=1   print instead of sending email
"""
import json, os, smtplib, sys, urllib.request
from datetime import datetime, timedelta, date
from email.message import EmailMessage
from zoneinfo import ZoneInfo

MAILBOX = "Rendezvous_ConsulatGeneralAlgerieaMontreal@consulatalgeriemontreal.ca"
API = f"https://bookings.cloud.microsoft/BookingsService/api/V1/bookingBusinessesc2/{MAILBOX}"
BOOKING_PAGE = f"https://bookings.cloud.microsoft/book/{MAILBOX}/"
TZ = ZoneInfo("America/Toronto")
OPEN = {"BOOKINGSAVAILABILITYSTATUS_AVAILABLE", "BOOKINGSAVAILABILITYSTATUS_SLOTS_AVAILABLE"}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def post(path, body):
    req = urllib.request.Request(
        f"{API}/{path}", data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", "x-req-source": "BookingsC2",
                 "x-anchormailbox": MAILBOX, "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def iso_duration_days(s, default=60):
    # "P46D" -> 46
    try:
        return int(s.strip("P").rstrip("D"))
    except Exception:
        return default


def bookable_minutes(policy, day: date):
    """Return list of (start_min, end_min) the service is bookable on `day`."""
    windows = policy.get("bookingServiceWindows") or []
    chosen = None
    for w in windows:
        if w.get("startDate") and w.get("endDate"):
            if date.fromisoformat(w["startDate"]) <= day <= date.fromisoformat(w["endDate"]):
                chosen = w
                break
    if chosen is None:
        chosen = next((w for w in windows if not w.get("startDate")), None)
    if chosen is None:  # no custom windows: rely on the server's answer
        return [(0, 24 * 60)]
    for h in chosen.get("bookableHours", []):
        if h["day"] == DAYS[day.weekday()]:
            return [(t["start"], t["end"]) for t in h["timeSlots"]]
    return []


def open_slots(service):
    pol = service["bookingsSchedulingPolicy"]
    step = 30
    now = datetime.now(TZ)
    earliest = now + timedelta(days=iso_duration_days(pol.get("minimumLeadTime", "P1D"), 1))
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=iso_duration_days(pol.get("maximumAdvance", "P60D")) + 1)
    groups = [g["staffGroupGuid"] for g in service.get("staffGroups") or []] or service["staffMemberIds"]
    fmt = "%Y-%m-%dT%H:%M:%S"
    data = post("GetStaffAvailability", {
        "serviceId": service["serviceId"], "groupStaffIds": groups,
        "startDateTime": {"dateTime": start.strftime(fmt), "timeZone": "Eastern Standard Time"},
        "endDateTime": {"dateTime": end.strftime(fmt), "timeZone": "Eastern Standard Time"}})
    slots = set()
    for staff in data.get("staffAvailabilityResponse", []):
        for it in staff.get("availabilityItems", []):
            if it["status"] not in OPEN:
                continue
            a = datetime.fromisoformat(it["startDateTime"]["dateTime"]).replace(tzinfo=TZ)
            b = datetime.fromisoformat(it["endDateTime"]["dateTime"]).replace(tzinfo=TZ)
            t = a
            while t + timedelta(minutes=step) <= b:
                m = t.hour * 60 + t.minute
                if t >= earliest and any(s <= m and m + step <= e for s, e in bookable_minutes(pol, t.date())):
                    slots.add(t)
                t += timedelta(minutes=step)
    return sorted(slots)


def send_email(subject, body):
    user, pwd = os.environ["SMTP_USER"], os.environ["SMTP_PASS"]
    to = [x.strip() for x in os.environ["EMAIL_TO"].split(",") if x.strip()]
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, user, ", ".join(to)
    msg.set_content(body)
    with smtplib.SMTP_SSL(os.environ.get("SMTP_HOST", "smtp.gmail.com"), 465) as s:
        s.login(user, pwd)
        s.send_message(msg)


def main():
    words = [w.strip().lower() for w in os.environ.get("SERVICE_MATCH", "carte nationale").split(",")]
    services = post("services", {"queryOptions": {}})["service"]
    wanted = [s for s in services if all(w in s["title"].lower() for w in words)]
    if not wanted:
        sys.exit(f"No service matches {words}. Services: {[s['title'] for s in services]}")

    state_file = os.environ.get("STATE_FILE", "state.json")
    try:
        seen = set(json.load(open(state_file)))
    except Exception:
        seen = set()

    lines, now_open = [], set()
    for svc in wanted:
        slots = open_slots(svc)
        title = svc["title"].lstrip("🟩🟦🟠 ").strip()
        print(f"{title}: {len(slots)} open slot(s)")
        keys = {f"{svc['serviceId']}|{t.isoformat()}" for t in slots}
        now_open |= keys
        new = [t for t in slots if f"{svc['serviceId']}|{t.isoformat()}" not in seen]
        if new:
            lines.append(f"{title}\n" + "\n".join(
                f"  • {t.strftime('%a %d %b %Y, %H:%M')}" + ("  (NEW)" if t in new else "") for t in slots)
                + f"\n  Réserver / Book: {svc.get('webUrl') or BOOKING_PAGE}\n")

    if lines:
        body = ("Des rendez-vous sont disponibles ! / Appointments are available!\n\n"
                + "\n".join(lines)
                + f"\nPage de réservation: {BOOKING_PAGE}\n"
                  "Heures: heure de Montréal (Eastern Time). Faites vite, ils partent rapidement.\n")
        subject = "🟢 RDV disponible – Passeport / Carte d'identité (Consulat Montréal)"
        if os.environ.get("DRY_RUN"):
            print(subject + "\n" + body)
        else:
            send_email(subject, body)
            print("Email sent.")
    # Remember only slots that are still open, so a slot that frees up again re-alerts.
    json.dump(sorted(now_open), open(state_file, "w"))


if __name__ == "__main__":
    main()
