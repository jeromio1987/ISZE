# SPA basket intake — getting the basket off the mail and into the builder

**For:** Jerome · **Written:** 2026-09-20 · internal only

## What this is for

A distributor sends the SPA basket as a spreadsheet attachment. Until now that
list was retyped into the optimizer, which is the step that put the wrong number
in the June application form. This note covers the two ways to get the
attachment onto the disk, and which one to use.

There are two pieces:

| Piece | Where | What it does |
|---|---|---|
| `fetch_spa_baskets_from_outlook.ps1` | `04_tools\spa_application\` | Reads a mailbox folder, saves the spreadsheets, ignores everything else |
| A mail rule (optional) | Outlook on the web | Files mail into one folder so the script has less to read |

---

## The finding you need to know before you create any rule

**A "has an attachment" rule does not mean what it sounds like.** Microsoft
states that the flag reacts to anything in the message that is labelled an
attachment in the message structure, and that this **includes the inline logos
and signature images** ([Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5698983/company-logo-and-signature-it-is-treating-as-an-at)).
There is no web-rule condition that separates a real file from a signature logo.

Measured on this mailbox, the 500 most recent Inbox messages:

| | Count |
|---|---|
| Messages with something attached | 272 |
| ... carrying a spreadsheet | 61 |
| ... carrying a non-image file | 37 |
| **... carrying only signature images** | **174 (64% of them)** |
| Non-spreadsheet attachments skipped by the script | 271 in the first 60 messages alone |

So a blanket "any attachment" rule would drag about **274 messages into the folder
for every 100 that actually carry a file**, and most of what it files is
signature noise. It would also do it to the whole Inbox, because a rule cannot be
told to leave the Inbox alone while copying - a *copy* rule leaves the original
where it is, so nothing moves, but the SPA folder fills with hundreds of mails
that have nothing in them.

**That is the trap.** The rule is not harmful, but it is not the filter. The
filter is the file type, and that lives in the script.

---

## Recommended: skip the rule, run the script

The script already reads the Inbox and keeps only `.xlsx .xls .xlsm .csv`,
skipping every signature image, and it de-duplicates by file hash so a re-run
never makes a copy. It does exactly what you asked for - any mail with a
spreadsheet in it, regardless of who sent it - without the rule.

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE
powershell -File .\04_tools\spa_application\fetch_spa_baskets_from_outlook.ps1 -DryRun
powershell -File .\04_tools\spa_application\fetch_spa_baskets_from_outlook.ps1
```

`-DryRun` lists what it would save and writes nothing. Run without it when the
list looks right.

Files land in `01_data\90_INBOX\_spa_baskets\`. That folder is already git-ignored,
so baskets never leave this machine.

---

## If you still want the folder, create it but do not point a rule at everything

Useful version of the rule: file only mail from the distributor domains that send
baskets, not every mail with a logo. That keeps the folder meaningful.

**Create the folder first** (exact name, including the space):

```
SPA attachments
```

**Then, in Outlook on the web:**

1. Open `https://outlook.cloud.microsoft/mail/` and sign in.
2. Click the **Settings** gear, top right.
3. Go to **Mail** then **Rules**.
4. Click **Add new rule**.
5. Name it exactly: `SPA basket attachments`
6. Under **Add a condition**, choose **From**, and add the distributor addresses
   you actually receive baskets from (for example the UTI and UMI contacts).
7. Add a second condition if you want it tighter - **Subject includes** with a
   word such as `SPA`.
8. Under **Add an action**, choose **Copy to**, then pick the folder
   **SPA attachments**. Use **Copy**, not **Move**.

   **Do not use Move.** A rule that moves will pull roughly 274 of every 500
   messages out of your Inbox and into that folder, and you would be reading your
   mail in the wrong place from then on. Copy leaves the mail where it is.
9. Leave **Stop processing more rules** unticked unless you know you want it.
10. Click **Save**.

Then point the script at that folder instead of the Inbox:

```powershell
powershell -File .\04_tools\spa_application\fetch_spa_baskets_from_outlook.ps1 -Folder "SPA attachments"
```

The rule runs on the mail server, so it works whether or not this PC is switched
on, and it follows your mailbox to any machine you sign in on.

---

## What the script needs, and what breaks it

**It needs classic desktop Outlook running on this PC.** It talks to Outlook over
COM, which is the same route the workspace already uses for mail.
Outlook is installed and running here now.

**When IT moves this machine to the new Outlook, this script stops working.**
The new Outlook does not expose COM, so the script cannot reach the mailbox at
all. It will say so plainly rather than failing quietly:

```
ABORTED - missing input: classic Outlook (no OUTLOOK.EXE found).
```

Microsoft lists **Save to disk** among the actions that only classic Outlook
supports, and states that the new Outlook and Outlook on the web run server-side
rules only, with client-side actions not supported
([rule feature table](https://support.microsoft.com/en-us/outlook/mail/edit-or-fix-a-broken-rule-in-outlook)).
So there is no version of this that survives that migration on this PC. The
durable alternative is a Power Automate flow, which can save the attachment to a
SharePoint or OneDrive folder without any Outlook client - see below.

**The script never touches your mail.** It does not move, copy, delete, flag,
mark read or send anything. It reads attachment content and writes new files to
local disk. Signature images are counted and reported as skipped.

---

## The cloud alternative, if you ever need it

A Power Automate flow can do the whole job without Outlook on a PC: trigger on a
new mail, loop the attachments, create the file in SharePoint or OneDrive. It uses
the standard Office 365 Outlook connector and the standard SharePoint connector,
which do not need a premium licence; it does need rights to the mailbox and
contributing rights to the target library
([Microsoft training](https://learn.microsoft.com/en-us/training/modules/get-started-flows/flow-monitor-incoming-emails)).

It is also the only route that can filter inline images properly, because the flow
can see the `isInline` flag on each attachment, which a rule cannot
([Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5698983/company-logo-and-signature-it-is-treating-as-an-at)).
Not built, and not needed while the PC route works.
