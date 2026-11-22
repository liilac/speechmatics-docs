---
name: account-administration
description: Administers a Speechmatics account through the portal and the Management API. Covers accounts and sign-in, workspaces, Admin and Member roles, inviting and removing members, domain verification, SSO (SAML, OIDC), projects, API keys, management tokens and their permissions, the Management API at `https://mp.speechmatics.com/v1` (`/projects`, `/api-keys`, `project_id`, `apikey_id`), billing, credits, Free, Pro, and Enterprise plans, discounts, usage reporting, regions, data retention, and security and compliance certifications. Use when automating project or API key creation, rotating or revoking keys, writing scripts with a management token, or answering questions about portal settings, invoices, pay-as-you-go, usage by model, data residency, HIPAA, SOC 2, or GDPR.
---

# Account administration

Manage a Speechmatics SaaS account: who has access, how work is organized, which credentials exist, and how usage is billed. Portal: https://portal.speechmatics.com

## When to use another skill

- Using an API key in a transcription request, temporary keys (JWTs), endpoint hostnames: `speechmatics:get-started`.
- Batch usage statistics endpoint and job deletion: `speechmatics:batch-transcription`.
- On-prem usage reporting: `speechmatics:container-deployment`.
- Aggregated analytics for an app where users bring their own keys (`sm-app`): `speechmatics:accuracy-benchmarking`.

## Resource model

```text
Workspace (members, roles, billing, usage, management tokens)
└── Project (default project plus up to 1000 total)
    └── API key (scoped to one project; sees only that project's transcripts)
```

- An account is one person's identity. It can belong to several workspaces, as Admin or Member in each.
- A workspace is the top-level container. It is not tied to a region.
- Any member of a workspace can access any project in it.
- Billing and usage belong to the workspace. They are not segmented by project, though usage can be viewed per project.

## Credentials: pick the right one

| Credential | Authenticates | Scope | Expires | Created |
|---|---|---|---|---|
| API key | STT and TTS requests | One project | No, until revoked | Portal, or Management API |
| Temporary key (JWT) | STT requests from end-user clients | Project of the API key that minted it | 60-86400 seconds | `POST /v1/jwts` with an API key (`speechmatics:get-started`) |
| Management token | Management API (workspace administration) | Workspace | No, until revoked | Portal only |

Token and key values are shown once at creation. Store them immediately.

## Roles

| Role | Capabilities |
|---|---|
| Admin | Full access: settings, billing, members, projects. Can invite and remove members, create and delete projects and API keys, and rename the workspace. |
| Member | Access to all workspace resources, including projects and usage. Cannot manage members, billing, or workspace settings. |

Admin is required for: member management, domain verification, SSO configuration, billing.

## Portal task map

| Task | Where in the portal |
|---|---|
| Profile, password, MFA, connected OAuth accounts, signed-in devices, delete account | **Settings > Profile** |
| Switch workspace | Avatar menu in the sidebar |
| Invite, edit role, remove users | **Manage workspace** (under **Workspace**) > **Users** |
| Verify a domain | **Manage workspace** > **Domain** > **Add domain** |
| Create, view, revoke management tokens | **Manage workspace** > **Management tokens** |
| Enable the model training discount | **Manage workspace** > **Model training** |
| Create or switch project | Projects dropdown in the top navigation |
| Rename or delete a project | **Settings > Projects** |
| Create or revoke API keys | **API keys** (under **Projects**), in the active project |
| Payment card, credits, invoices | **Billing** (under **Workspace**) |
| Usage charts | **Usage** (under **Workspace**) |
| Region for portal transcription | **Region** selector in the top navigation |

## Management API

Base URL: `https://mp.speechmatics.com/v1`. Authenticate with a management token: `Authorization: Bearer YOUR_MANAGEMENT_TOKEN`.

| Operation | Method and path |
|---|---|
| Get all projects | `GET /projects` |
| Create a project | `POST /projects` |
| Get a project by ID | `GET /projects/{project_id}` |
| Update a project | `PUT /projects/{project_id}` |
| Delete a project | `DELETE /projects/{project_id}` |
| Get all API keys | `GET /api-keys?project_id={project_id}` |
| Create an API key | `POST /api-keys` |
| Delete an API key | `DELETE /api-keys/{apikey_id}` |

### Create a management token

1. Go to **Manage workspace** in the sidebar under **Workspace**.
2. In **Management tokens**, click **+ Create management token**.
3. Name it after its purpose, such as `ci-pipeline` or `key-rotation-script`.
4. Select only the permissions the automation needs: View projects, Manage projects, View API keys, Create API key, Delete API keys.
5. Click **Create management token** and copy the value from the **Save your key** dialog.

### Create a project and issue its API key

```bash
MANAGEMENT_TOKEN="YOUR_MANAGEMENT_TOKEN"

curl -L -X POST "https://mp.speechmatics.com/v1/projects" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Customer support", "description": "Transcribes support calls"}'
```

The `201` response is a `Project` object. Take its `project_id` (an integer) and create a permanent key:

```bash
curl -L -X POST "https://mp.speechmatics.com/v1/api-keys?type=batch" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 12345, "name": "ci-pipeline"}'
```

The `201` response contains `apikey_id` and `key_value`. `key_value` is the secret; `apikey_id` is what you pass to delete the key.

### Rotate a key

1. `POST /api-keys` with the same `project_id` and a new `name`.
2. Deploy the new `key_value`.
3. `DELETE /api-keys/{apikey_id}` for the old key. Revocation is immediate.

```bash
curl -L -X DELETE "https://mp.speechmatics.com/v1/api-keys/${APIKEY_ID}" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}"
```

Full schemas, every status code, and all code samples: [references/management-api.md](references/management-api.md).

## Billing and plans in brief

- Billing is in credits. One credit is worth one US dollar. New sign-ups get a $100 credit grant.
- Free: use the granted credits, no payment card.
- Pro: add a payment card on the Billing page. Usage draws down granted credits first; the rest is charged to the card on the first of each month for the previous month, calculated to the exact second at the per-hour rate for each product type.
- Enterprise: contract-based, no card or portal billing. Required for on-prem and on-device deployment.
- Pro discounts (stackable): model training (data logging) and an automatic volume discount above 500 billable hours per month per STT product type.
- Prices are not in the docs. Point to https://www.speechmatics.com/pricing.

Details: [references/billing-plans-usage.md](references/billing-plans-usage.md).

## Usage in brief

- Portal: **Usage** shows **Realtime** and **Batch** charts by model, with total time and request count, filterable by time range (**7D**, **30D**, **Custom**) and project.
- Enhanced Medical and agent variants are reported under their underlying model.
- Portal usage covers cloud usage only.
- The Usage API reports Batch usage only: https://docs.speechmatics.com/api-ref/batch/get-usage-statistics

## Regions and data in brief

- Regions available to all customers: EU1 (Europe), US1 (United States), AU1 (Australia). Batch and Realtime run in all three.
- The endpoint called determines the region. A job lives in the region that created it; retrieve it from the same endpoint.
- Realtime: audio and transcripts are never stored. Batch: audio, transcripts, and job config are stored for 7 days, then deleted automatically; delete sooner with the API.
- Certifications and standards: ISO/IEC 27001:2022, SOC 2 Type II, GDPR, HIPAA. Documents come from the Trust Center: https://speechmatics.safebase.us/

Details: [references/regions-security.md](references/regions-security.md).

## Gotchas

- Deleting a project permanently removes its transcripts, usage history, and API keys. The default project cannot be deleted.
- Removing a user does not revoke API keys they created. Keys belong to the workspace; revoke them separately.
- Revoking a management token cannot be undone and takes effect immediately.
- An account cannot be deleted while it is Admin in multiple workspaces. A deleted account's email address cannot be reused.
- `DELETE /projects/{project_id}` returns `403` most probably because of outstanding payments. `POST /api-keys` returns `403` when the project already has the maximum number of API keys.
- A long-lived API key can call `POST /api-keys` only to create temporary keys. Permanent keys need a management token. For temporary keys the authentication docs direct you to `POST /v1/jwts`.
- More than 1000 projects: use temporary keys with `client_ref` to isolate end users instead, or contact support@speechmatics.com.
- SSO is a paid add-on enabled by support, not self-serve.
- You never pass a project ID to the transcription APIs. The API key determines the project.

## References

- [references/management-api.md](references/management-api.md): every Management API endpoint, parameter, schema, status code, and code sample; management token permissions and lifecycle. Read when writing automation.
- [references/workspaces-members-sso.md](references/workspaces-members-sso.md): accounts, sign-in, workspaces, roles, member management, domain verification, SSO. Read for access and identity questions.
- [references/projects-and-api-keys.md](references/projects-and-api-keys.md): project behavior and limits, API key lifecycle in the portal, best practices. Read when structuring environments or tenants.
- [references/billing-plans-usage.md](references/billing-plans-usage.md): credits, PAYG, payment cards, invoice statuses, plans, discounts, usage reporting. Read for cost and invoice questions.
- [references/regions-security.md](references/regions-security.md): regions, multi-region use, data handling, certifications, Trust Center. Read for residency and compliance questions.
