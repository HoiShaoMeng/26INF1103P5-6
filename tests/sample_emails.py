# Sample reported emails for manually testing the AI prompt (not used by the automated tests).
# Each one notes the classification and threat_level we expect the AI to return.

SAMPLE_EMAILS = {
    # Expected: spear-phishing, threat_level 80-95
    "spear_phishing_ceo": {
        "sender_email": "john.tan@yourcompany-support.com",
        "sender_name": "John Tan (CEO)",
        "subject": "Quick favor - urgent wire transfer",
        "body": (
            "Hi Sarah,\n\n"
            "I'm stuck in a meeting and can't call. Can you process an urgent wire "
            "transfer of $8,500 to our new vendor today? I'll send the account "
            "details shortly. Please keep this between us for now, it's time "
            "sensitive.\n\n"
            "Thanks,\nJohn"
        ),
        "urls": [],
        "attachments": [],
    },
 
    # Expected: phishing, threat_level 80-95 (malicious attachment)
    "phishing_fake_invoice": {
        "sender_email": "billing@acc0unts-payable.net",
        "sender_name": "Accounts Payable",
        "subject": "Overdue invoice #INV-20931 - final notice",
        "body": (
            "Hello,\n\n"
            "Your payment for the attached invoice is now 30 days overdue. Please "
            "open the attached file and enable macros to view the full breakdown. "
            "Failure to pay within 48 hours will result in legal action.\n\n"
            "Regards,\nAccounts Payable"
        ),
        "urls": [],
        "attachments": [
            {"filename": "INV-20931.pdf.exe", "extension": "exe"},
            {"filename": "payment_details.docm", "extension": "docm"},
        ],
    },

    # Expected: phishing, threat_level 50-75 (IT impersonation, softer tone)
    "borderline_it_mailbox": {
        "sender_email": "it-helpdesk@yourcompany-mail.org",
        "sender_name": "IT Helpdesk",
        "subject": "Mailbox storage almost full",
        "body": (
            "Hi,\n\n"
            "Your mailbox has reached 95% of its storage limit. To avoid losing "
            "incoming emails, please log in to the portal below to increase your "
            "quota.\n\n"
            "IT Helpdesk"
        ),
        "urls": ["https://yourcompany-mail.org/quota-upgrade"],
        "attachments": [],
    },

    # Expected: spam, threat_level 15-35
    "spam_newsletter": {
        "sender_email": "news@crypto-daily-insider.info",
        "sender_name": "Crypto Daily Insider",
        "subject": "This coin could 100x next week",
        "body": (
            "Our analysts have found the next big thing in crypto. Subscribers "
            "who got in early last month saw huge returns. Read the full report "
            "on our website."
        ),
        "urls": ["http://crypto-daily-insider.info/report"],
        "attachments": [],
    },
   
    # Expected: benign, threat_level 0-15 (false-positive test)
    "benign_security_alert": {
        "sender_email": "no-reply@accounts.google.com",
        "sender_name": "Google",
        "subject": "Security alert: New sign-in from Windows device",
        "body": (
            "We noticed a new sign-in to your Google Account on a Windows device. "
            "If this was you, no action is needed. If not, we recommend securing "
            "your account."
        ),
        "urls": ["https://myaccount.google.com/notifications"],
        "attachments": [],
    },
 
    # Expected: benign, threat_level 0-15 (legit attachment from internal sender)
    "benign_meeting_notes": {
        "sender_email": "mei.lin@yourcompany.com",
        "sender_name": "Mei Lin",
        "subject": "Notes from Monday's project meeting",
        "body": (
            "Hi all,\n\n"
            "Attached are the notes from Monday's meeting. Please review the action "
            "items assigned to you before our next check-in on Thursday.\n\n"
            "Mei Lin"
        ),
        "urls": [],
        "attachments": [
            {"filename": "meeting_notes_2026-09-28.pdf", "extension": "pdf"},
        ],
    },
}
