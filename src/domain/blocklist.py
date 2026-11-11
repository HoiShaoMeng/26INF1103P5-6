"""blocklist: senders an analyst has confirmed as phishing, so the same attacker cannot get through twice."""


#the set of blocked entries. an entry is a whole domain (evil.com), or one exact address for
#public mail providers, because blocking all of gmail.com would block every gmail user.
class Blocklist:

    #shared by every Blocklist: domains anyone can sign up to, so only the exact address is ever blocked
    PUBLIC_MAIL_DOMAINS = frozenset({
        "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
        "yahoo.com", "icloud.com", "proton.me", "protonmail.com",
    })

    def __init__(self, entries: list | None = None):
        #private set: no duplicates, and outside code can only change it through block_sender()
        self._entries = set()
        for entry in entries or []:
            if isinstance(entry, str) and entry.strip():
                self._entries.add(entry.strip().lower())

    #which entry would block this sender: "evil.com" for a company domain, "bob@gmail.com" for a public one.
    #"" if the address has no domain, so it can never be blocked by mistake.
    @classmethod
    def entry_for(cls, sender_email: str) -> str:
        if not isinstance(sender_email, str) or "@" not in sender_email:
            return ""
        address = sender_email.strip().lower()
        domain = address.rsplit("@", 1)[1]
        if not domain:
            return ""
        if domain in cls.PUBLIC_MAIL_DOMAINS:
            return address
        return domain

    #True if this sender's domain (or exact public address) is blocked
    def contains_sender(self, sender_email: str) -> bool:
        entry = self.entry_for(sender_email)
        return entry != "" and entry in self._entries

    #blocks this sender and returns the entry that was added, or "" if the address could not be blocked
    def block_sender(self, sender_email: str) -> str:
        entry = self.entry_for(sender_email)
        if entry:
            self._entries.add(entry)
        return entry

    #read-only, sorted copy so the saved file is always in the same order
    @property
    def entries(self) -> list:
        return sorted(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
