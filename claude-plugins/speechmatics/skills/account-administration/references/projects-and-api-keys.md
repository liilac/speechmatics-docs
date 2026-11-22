# Projects and API keys

Sources:

- https://docs.speechmatics.com/administration/projects
- https://docs.speechmatics.com/administration/api-keys

## Projects

A project is an organizational unit inside a workspace. API keys and the transcripts they produce belong to a project. Any member of the workspace can access any project in it.

### Rules and limits

- Each workspace starts with a default project, which cannot be deleted.
- A workspace can have up to 1000 projects. If you need more, use temporary keys (see `speechmatics:get-started`) or contact support@speechmatics.com.
- API keys are scoped to a single project: a key created in one project cannot access transcripts produced in another.
- Billing and usage are not segmented by project, though usage can be viewed per project.
- The project ID is read-only.
- When using the API you do not specify a project. Each API key is tied to one project, so the key determines the project a request applies to.

### Common use cases

- Development workflows: separate development, staging, and production.
- Organization segmentation: monitor usage by product line, department, or business unit.
- Multi-client service providers: give each client their own API keys and isolate their transcripts and usage data.

### Create a project

1. Open the projects dropdown in the top navigation.
2. Select **Create project**.
3. Enter a descriptive name.
4. Click **Create**.

### Switch between projects

The active project is shown in the top navigation. Transcribing in the portal and managing API keys both apply to the active project.

1. Click the projects dropdown.
2. Select a project.

### Rename or delete a project

Manage projects under **Settings > Projects**.

Deleting a project permanently removes all of its transcripts, usage history, and API keys. This cannot be undone.

### Manage projects with the API

Use the Management API with a management token. Operations: get all projects, get a project by ID, create a project, update a project, delete a project. See [management-api.md](management-api.md).

## API keys

An API key authenticates requests to the Speech to Text and Text to Speech APIs. Each key is scoped to a single project and can access only the transcripts produced within that project.

### API keys versus management tokens

| | API key | Management token |
|---|---|---|
| Authenticates | Transcription and synthesis requests | Workspace administration (Management API) |
| Scope | Project | Workspace |

### Create an API key in the portal

Keys are created in the active project. To create one in a different project, switch projects first.

1. Go to **API keys** in the sidebar under **Projects**.
2. Click **Create new key**.
3. Enter a descriptive name.
4. Click **Generate new key**.
5. Copy the key value from the dialog.

The key value cannot be accessed again after the dialog closes. Store it in a secure location immediately.

Direct link used elsewhere in the docs: https://portal.speechmatics.com/settings/api-keys/

### Revoke an API key

Revoking disables the key immediately. Requests made with it are rejected, which may break any application that depends on it.

1. Go to **API keys** in the sidebar under **Projects**.
2. Click the delete button next to the key.
3. Confirm.

### Manage API keys with the API

Use the Management API with a management token. Operations: get all API keys, create an API key, delete an API key. See [management-api.md](management-api.md).

### Best practices

- Use descriptive names. Name keys after the application or environment that uses them, so the right key can be audited and revoked later.
- Scope keys to projects. Create keys in the project that matches their purpose to keep transcripts and usage isolated.
- Rotate keys periodically. Create a replacement key, update the application, then revoke the old one.
- Revoke unused keys.
- Store and grant access on the principle of least privilege. If a key is compromised, contact support at https://support.speechmatics.com.
- Do not expose long-lived keys to end users or browsers. Use temporary keys (`speechmatics:get-started`).

## Choosing an isolation strategy

| Need | Approach |
|---|---|
| Separate environments or business units | One project per environment or unit, with its own keys |
| Per-client isolation of transcripts and usage, up to 1000 clients | One project per client |
| Per-end-user isolation of Batch jobs at larger scale | Temporary keys with a unique `client_ref` per end user |
| Key belongs to someone who left | Keys belong to the workspace, not the user. Revoke and reissue if needed |
