# DiliBot — Terms of Service

**Effective date:** July 20, 2026
**Last updated:** July 20, 2026

These Terms of Service ("Terms") govern your use of the DiliBot Discord bot ("DiliBot", "the Bot", "we", "us", or "our"). By adding the Bot to a Discord server, or by using any of its commands, you ("you" or "the user") agree to these Terms. If you do not agree, do not add or use the Bot, and remove it from any server you control.

These Terms apply both to the server administrators who add and configure the Bot and to all members of servers where the Bot is present.

---

## 1. Description of Service

DiliBot is a Discord bot that audits raid signups. When invoked through its `/audit` slash command with a Raid-Helper event ID, the Bot compares the members of your server who hold a configured role (default: **Raider**) against the list of participants signed up for that Raid-Helper event, and reports which of those members have not signed up.

The Bot is provided **free of charge** and is intended for use by Discord communities that organize raids.

---

## 2. Eligibility

By using the Bot, you represent that:

- You are at least **13 years old**, or the minimum age required to use Discord in your country, whichever is greater.
- You will comply with the [Discord Terms of Service](https://discord.com/terms) and [Community Guidelines](https://discord.com/guidelines) at all times.
- If you add or configure the Bot for a server, you have the authority (appropriate permissions) to do so on behalf of that server.

---

## 3. Acceptable Use

You agree **not** to:

- Use the Bot for any unlawful purpose or in violation of Discord's Terms of Service or Community Guidelines;
- Attempt to disrupt, overload, abuse, reverse engineer, probe, or gain unauthorized access to the Bot or the infrastructure it runs on;
- Use automated means to flood, spam, or otherwise abuse the Bot's commands;
- Use the Bot to harass, defame, discriminate against, or otherwise harm other users.

We reserve the right to restrict, suspend, or revoke access to the Bot for any user or server that violates these Terms, at our sole discretion and without prior notice.

---

## 4. Data Handling

DiliBot processes the following information **only when a command is run**, and solely to produce the audit result:

- Discord user IDs, usernames, and display names (nicknames) of members in your server;
- Role membership of members within your server;
- Signup data retrieved from the Raid-Helper API for the event ID you provide.

**DiliBot does not operate a database and does not persistently store your server's member data, role data, or audit results.** This information is processed in memory to generate the response to a single command and is discarded once that response is delivered. Diagnostic logs generated during operation are retained only temporarily for troubleshooting and expire automatically.

To read your server's member list, the Bot requires Discord's **Server Members Intent**. By adding and authorizing the Bot, the server administrator consents to this access.

> The Bot's [Privacy Policy](PRIVACY_POLICY.md) forms part of these Terms and provides further detail on data handling.

---

## 5. Third-Party Services

DiliBot depends on the following third-party services, each governed by its own terms:

- **Discord** — the platform on which the Bot operates ([Discord Terms](https://discord.com/terms));
- **Raid-Helper** — the source of raid event signup data;
- **Amazon Web Services (AWS)** — the hosting infrastructure.

Your use of the Bot is also subject to the terms and policies of these providers. We are not responsible for the availability, accuracy, conduct, or content of any third-party service, and outages or changes in those services may affect the Bot.

---

## 6. Availability and Disclaimer of Warranty

The Bot is provided **"as is"** and **"as available"**, without warranties of any kind, whether express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, accuracy, reliability, or non-infringement.

We do not warrant that the Bot will be uninterrupted, available at any given time, error-free, or that its audit results will be complete or accurate. Audit results depend on data supplied by Discord and Raid-Helper, which may be incomplete, delayed, or out of date. **You are responsible for verifying any result before relying on it.**

---

## 7. Limitation of Liability

To the maximum extent permitted by applicable law, in no event shall the developer(s) of the Bot be liable for any indirect, incidental, special, consequential, or punitive damages, or for any loss of data, profits, goodwill, or other intangible losses, arising out of or in connection with your use of, or inability to use, the Bot — even if advised of the possibility of such damages.

---

## 8. Termination

You may stop using the Bot at any time by removing it from your server. We reserve the right to modify, suspend, or discontinue the Bot — in whole or in part — at any time and without notice or liability.

---

## 9. Changes to These Terms

We may update these Terms from time to time. When we do, we will revise the "Last updated" date above and publish the updated document to the Bot's repository. Your continued use of the Bot after changes are published constitutes acceptance of the revised Terms.

---

## 10. Governing Law

These Terms are governed by and construed in accordance with the laws of United States, without regard to its conflict-of-law provisions.

---

## 11. Contact

Questions about these Terms can be directed to the developer via the project's GitHub repository:

- **Repository:** https://github.com/kalesec/DiliBot
- **Discord Contact:** .muraa.

---