# ReelVault AI

**AI-powered opportunity verification, scam warnings, and deadline reminders**

ReelVault AI helps students verify opportunities shared through social media reels before acting on them. It extracts opportunity details, identifies verifiable claims, gathers external evidence, evaluates credibility, flags potential scam indicators, and helps users save opportunities and deadlines.

## Key Features

- **Opportunity extraction:** Extract titles, organizers, eligibility, rewards, fees, application links, and deadlines.
- **Claim verification:** Evaluate individual claims against external evidence.
- **Evidence collection:** Find relevant sources and provide supporting links.
- **Scam warnings:** Flag suspicious payment requests, misleading benefits, and inconsistent information.
- **Opportunity cards:** Save verified analysis and important opportunity details.
- **Deadline reminders:** Save deadlines to the Vault and support calendar integration where configured.
- **Persistent verification history:** Store each verification run and its stages in Supabase.
- **Resume incomplete runs:** Continue from the last completed stage.
- **URL verification:** Preserve the existing URL-based verification functionality.

## Verification Workflow

Each verification run follows this exact sequence:

`Extracted → Claims → Evidence → Verdict → Card`

| Stage | Purpose |
|---|---|
| 1. Extracted | Extract opportunity details from the supplied content. |
| 2. Claims | Separate the content into individual verifiable claims. |
| 3. Evidence | Collect relevant external evidence for the claims. |
| 4. Verdict | Evaluate each claim using the available evidence. |
| 5. Card | Generate the final opportunity card after the first four stages are saved successfully. |

**Important:** The Card stage must not be created unless the Extracted, Claims, Evidence, and Verdict stages have all been persisted for the same verification run.

## AI Prompts

The following concise prompts document the intended AI workflow. Confirm that they match the prompts actually used by the backend before describing them as the exact production prompts.

### 1. Extracted — Opportunity Extraction

```text
Analyze the transcript, on-screen text, and metadata. Extract the opportunity title, organizer, eligibility, benefits, fees, application link, and deadlines. Use external research when needed. Mark unknown details explicitly and never invent information.
```

### 2. Claims — Claim Identification

```text
Break the extracted content into specific, independently verifiable claims. Include claims about rewards, eligibility, deadlines, organizers, registration fees, and application requirements. Do not assume that any claim is true or false.
```

### 3. Evidence — Evidence Collection

```text
Find relevant evidence for every claim. Prioritize official organizer websites, government portals, and original announcements. Record source URLs and explain which claims each source supports or contradicts. Never fabricate sources or evidence.
```

### 4. Verdict — Claim Verification

```text
Evaluate each claim against the collected evidence. Assign exactly one verdict: supported, partially supported, contradicted, or insufficient evidence. Explain the reasoning and cite relevant sources. Missing evidence alone does not prove fraud.
```

### 5. Scam Warning — Risk Assessment

```text
Identify warning signs such as advance-payment demands, suspicious links, impersonation, unrealistic rewards, and inconsistent details. Flag payment required before applying as a potential-scam warning. A fee alone does not prove fraud. Explain the evidence behind each warning.
```

### 6. Card — Opportunity Card Generation

```text
Generate an opportunity card only after the Extracted, Claims, Evidence, and Verdict stages are successfully saved for the same run. Include opportunity details, claim verdicts, evidence links, warnings, deadlines, and reminder information. Never invent missing details or bypass stage prerequisites.
```

### 7. Source Classification

```text
Classify each source as an official website, government portal, organizer announcement, news article, or unverified social-media post. Assess credibility, relevance, and direct support for the claim. Prefer primary sources and explain limitations.
```

## Required Claim Verdicts

Every evaluated claim must use exactly one of these labels:

- `supported` — Reliable evidence supports the claim.
- `partially supported` — Evidence supports only part of the claim.
- `contradicted` — Reliable evidence conflicts with the claim.
- `insufficient evidence` — Available evidence is inadequate to reach a conclusion.

A verdict applies to an individual claim; it should not automatically determine the status of the entire opportunity.

## Potential Scam Warning Rules

ReelVault AI should distinguish suspicious indicators from proven fraud.

- Flag requests for payment before applying as a potential-scam warning.
- A registration fee alone is not proof of fraud.
- Check whether the organizer and opportunity can be corroborated through reliable sources.
- Flag suspicious links, impersonation, inconsistent details, and unrealistic promises when evidence supports those concerns.
- If evidence is insufficient, communicate the uncertainty instead of presenting an unsupported fraud accusation.

## Input Format: `.rvpack`

A verification pack can contain three sections:

```text
TRANSCRIPT:
₹80,000 for every 12th pass student. Apply before 31 Oct. Pay ₹500 to register. Link in bio.

ON_SCREEN:
₹80,000 FOR EVERY 12TH PASS STUDENT
Apply before Oct 31

META:
creator: opportunity.daily posted: 2026-10-05 url: none
```

### Expected Processing

1. Extract the opportunity details and claims.
2. Research the claims using relevant external sources.
3. Evaluate each claim using the required verdict labels.
4. Flag the advance-payment request for further verification.
5. Resolve the deadline using the available date context; if the year remains uncertain, request confirmation rather than inventing it.
6. Save the completed stages and create the opportunity card only after the prerequisites are met.
7. Save the deadline to the Vault reminder system when sufficient date information is available.

## Supabase Persistence

Verification runs use separate records for each stage.

Expected tables:

- `public.verification_runs`
- `public.verification_stages`

The intended behavior is:

- Each verification has its own run identifier.
- Each completed stage is persisted separately.
- Stages are saved in the required order.
- The Card stage requires the first four stages to exist for the same run.
- Opening a run displays its completed stages.
- An incomplete run resumes from the last successfully completed stage.
- Existing URL-verification cards remain accessible.

Apply the project's Supabase migrations before using the database-backed workflow. Ensure authentication, database permissions, and row-level security policies are configured for the intended users.

## Setup and Configuration

1. Clone or download the repository.
2. Install the backend dependencies listed in the server's dependency file.
3. Install the frontend dependencies listed in the client's package file.
4. Configure the environment variables required by the backend and frontend.
5. Apply the supplied Supabase migrations.
6. Start the backend and frontend using the project's configured development commands.

### Environment Variables

Use the repository's `.env.example` files as the source of truth for required variable names. Configure the applicable Supabase credentials, AI provider keys, evidence-search credentials, and frontend API URL.

**Security:** Keep secret keys in environment variables. Do not commit `.env` files or expose service-role keys in frontend code.

## Testing

Before submitting or deploying, verify that:

- The supplied `.rvpack` sample can be processed end to end.
- Every claim receives one of the four required verdict labels.
- Advance-payment requests produce a potential-scam warning when applicable.
- Unsupported claims are not automatically labelled fraudulent.
- Stage records are persisted in the correct order.
- Card creation is blocked when any prerequisite stage is missing.
- Incomplete runs resume correctly.
- Deadlines appear in the expected reminder interface.
- Existing URL verification and previously saved cards still work.
- Missing metadata and incomplete AI responses do not crash the pipeline.

Document test results only after running the tests against the relevant implementation.

## Limitations

- External evidence may be incomplete, unavailable, or outdated.
- AI-generated assessments are not guarantees that an opportunity is legitimate.
- Ambiguous deadlines may require user confirmation.
- Calendar and notification behavior depends on the integrations configured in the application.
- Prompt examples in this README may differ from the production prompts until verified against the backend source code.

## Project Goal

ReelVault AI aims to help students make better-informed decisions about opportunities discovered on social media by combining structured extraction, evidence-based claim verification, transparent risk warnings, persistent records, and deadline management.
