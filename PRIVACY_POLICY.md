# DiliBot — Privacy Policy

**Effective date:** July 20, 2026
**Last updated:** July 20, 2026

This Privacy Policy explains what information the DiliBot Discord bot ("DiliBot", "the Bot", "we", "us", or "our") processes, how it is used, and how it is protected. It should be read together with the [Terms of Service](TERMS_OF_SERVICE.md). By adding the Bot to a Discord server or using its commands, you acknowledge the practices described here.

**Summary:** DiliBot has no database. It reads the information it needs to answer a single `/audit` command, produces a result, and discards that information. It does not sell, share, or persistently store your data.

---

## 1. Information We Process

DiliBot processes the following information **only at the moment a command is run**, and only to produce the audit result:

| Data | Source | Why it is processed |
|------|--------|---------------------|
| Discord user IDs | Discord API | To match members against event signups |
| Usernames and display names (nicknames) | Discord API | To display who has not signed up |
| Role membership within your server | Discord API | To identify members holding the configured role (default: **Raider**) |
| Raid-Helper event signup data (participant user IDs) | Raid-Helper API | To determine who is signed up for the event |
| The Raid-Helper event ID you supply | Your command input | To look up the correct event |

DiliBot does **not** access or process the content of your messages, direct messages, voice activity, payment information, or any data unrelated to the audit command.

---

## 2. How We Use Information

The information above is used for a single purpose: **to generate the response to the `/audit` command** — a list of members holding the configured role who have not signed up for the specified Raid-Helper event.

We do **not**:

- Sell, rent, or trade your information;
- Use your information for advertising or profiling;
- Share your information with third parties except the service providers strictly required to operate the Bot (see Section 4).

---

## 3. Data Storage and Retention

- **No database.** DiliBot does not maintain a database and does not persistently store member data, role data, event data, or audit results.
- **In-memory processing.** The information in Section 1 is held only in memory for the brief duration of processing a command, and is discarded once the response is delivered.
- **Operational logs.** The Bot's hosting environment generates diagnostic logs for troubleshooting and reliability. These logs are retained for a limited period (currently up to **two weeks**) and are then automatically deleted. Logs are used only for operating and debugging the Bot and are not used to build profiles of users.

---

## 4. Third-Party Service Providers

DiliBot relies on the following third parties to function. Data is transmitted to or from these services only as needed to operate the Bot, and each is governed by its own privacy policy:

- **Discord** — the platform the Bot runs on and the source of member and role information. See the [Discord Privacy Policy](https://discord.com/privacy).
- **Raid-Helper** — queried to retrieve event signup data for the event ID you provide.
- **Amazon Web Services (AWS)** — hosts the Bot's code and stores its operational credentials.

We are not responsible for the privacy practices of these third parties.

---

## 5. Permissions and Discord Intents

To read your server's member list and their roles, DiliBot requires Discord's **Server Members Intent** (a privileged intent). By adding and authorizing the Bot, the server administrator consents to this access on behalf of the server. The Bot requests only the permissions necessary to perform audits (such as viewing channels, reading message history, and sending messages).

---

## 6. Data Security

We take reasonable measures to protect the Bot and the limited data it handles, including:

- The Bot's authentication token is stored as an encrypted secret and is never exposed in the Bot's public-facing components or logs.
- The public endpoint that receives commands cryptographically verifies that each request genuinely originates from Discord before taking any action.
- Because no user data is persistently stored, there is no standing database of personal information that could be exposed.

No method of transmission or storage is completely secure, and we cannot guarantee absolute security.

---

## 7. Children's Privacy

DiliBot is not directed to children under the age required to use Discord (at least **13**, or older where local law requires). We do not knowingly collect personal information from children. Because the Bot does not persistently store data, any information processed for a command is discarded after the response is delivered.

---

## 8. Your Rights

Depending on your jurisdiction, you may have rights to access, correct, or delete personal information held about you. Because DiliBot does **not persistently store** personal information, there is generally no stored data to access or delete beyond short-lived operational logs, which expire automatically.

If you have questions or wish to make a request regarding your information, contact us using the details in Section 10. Server administrators can remove the Bot from a server at any time to end all processing for that server.

---

## 9. Changes to This Policy

We may update this Privacy Policy from time to time. When we do, we will revise the "Last updated" date above and publish the updated document to the Bot's repository. Your continued use of the Bot after changes are published constitutes acceptance of the revised policy.

---

## 10. Contact

Questions about this Privacy Policy can be directed to the developer via the project's GitHub repository:

- **Repository:** https://github.com/kalesec/DiliBot
- **Discord Contact:** .muraa.

---