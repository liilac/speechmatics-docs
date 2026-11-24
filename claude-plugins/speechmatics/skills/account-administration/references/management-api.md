# Management API and management tokens

Sources:

- https://docs.speechmatics.com/administration/management-tokens
- https://docs.speechmatics.com/api-ref/management/create-an-api-key (and sibling pages under `/api-ref/management/`)
- OpenAPI spec `spec/mp.yaml` (Management API, version 1.0.0)

The Management API manages projects and API keys in a workspace programmatically, for example creating a project and issuing its API key from a CI pipeline.

## Base URL and authentication

```text
https://mp.speechmatics.com/v1
Authorization: Bearer YOUR_MANAGEMENT_TOKEN
```

- Default security for every operation: a management token (HTTP bearer), scoped to the workspace.
- `POST /api-keys` also accepts a long-lived API key as the bearer token, but an API key can create only temporary keys. Creating a permanent key needs a management token.
- Support contact in the spec: support@speechmatics.com.

## Management tokens

Management tokens authenticate programmatic workspace administration. They are scoped to the workspace and do not expire unless revoked. Each token is assigned a subset of permissions.

### Permissions

| Permission | Description |
|---|---|
| View projects | View projects created within your workspace. |
| Manage projects | Manage, edit, and delete projects in your workspace. |
| View API keys | View API keys generated in your workspace. |
| Delete API keys | Delete API keys in your workspace. |
| Create API key | Create API keys in your workspace. |

### Create

1. Go to **Manage workspace** in the sidebar under **Workspace**.
2. In the **Management tokens** section, click **+ Create management token**.
3. Enter a descriptive name.
4. Select the permissions the automation needs.
5. Click **Create management token**.
6. Copy the token value from the **Save your key** dialog. It cannot be shown again.

### View details

In the **Management tokens** table, open the options menu next to the token and select **View details**. The panel shows the token name, key prefix, last used timestamp, assigned permissions, and creation date.

### Revoke

Revoking disables the token immediately and cannot be undone. Requests made with it are rejected.

1. In the **Management tokens** table, open the options menu next to the token.
2. Select **Revoke key**.
3. Review the token name and key in the confirmation dialog.
4. Click **Revoke key**.

### Best practices

- Limit permissions. A token that creates API keys does not need permission to delete them.
- Use descriptive names, such as `ci-pipeline` or `key-rotation-script`.
- Rotate periodically: create a replacement, update systems, revoke the old one.
- Revoke unused tokens. Check the **Last used** column regularly.

## Endpoints

### GET /projects

Get all projects. No parameters.

```bash
MANAGEMENT_TOKEN="YOUR_MANAGEMENT_TOKEN"

curl -L -X GET "https://mp.speechmatics.com/v1/projects" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}"
```

| Status | Meaning | Body |
|---|---|---|
| 200 | OK | Array of `Project` |
| 404 | Not Found | `ErrorResponse` |
| 410 | Gone | `ErrorResponse` |
| 500 | Internal Server Error | `ErrorResponse` |

Docs: https://docs.speechmatics.com/api-ref/management/get-all-projects

### POST /projects

Create a project. Request body required (`CreateProjectRequest`).

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | The name of the project |
| `description` | string | No | A description of the project and its intended use |
| `contract_id` | integer (int64) | No | Optional, kept for backward compatibility. The contract the project should be created under |

```bash
MANAGEMENT_TOKEN="YOUR_MANAGEMENT_TOKEN"

curl -L -X POST "https://mp.speechmatics.com/v1/projects" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Customer support", "description": "Transcribes support calls"}'
```

| Status | Meaning | Body |
|---|---|---|
| 201 | Created | `Project` |
| 410 | Gone | `ErrorResponse` |
| 500 | Internal Server Error | `ErrorResponse` |

Docs: https://docs.speechmatics.com/api-ref/management/create-a-project

### GET /projects/{project_id}

Get a project by ID. Path parameter `project_id`: integer (int64), required.

```bash
MANAGEMENT_TOKEN="YOUR_MANAGEMENT_TOKEN"
PROJECT_ID="12345"

curl -L -X GET "https://mp.speechmatics.com/v1/projects/${PROJECT_ID}" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}"
```

| Status | Meaning | Body |
|---|---|---|
| 200 | OK | `Project` |
| 400 | Bad Request | `ErrorResponse` |
| 401 | Unauthorized | `ErrorResponse` |
| 404 | Project was not found | `ErrorResponse` |
| 410 | Project Gone | `ErrorResponse` |
| 500 | Internal Server Error | `ErrorResponse` |

Docs: https://docs.speechmatics.com/api-ref/management/get-a-project-by-id

### PUT /projects/{project_id}

Update a project. Path parameter `project_id`: integer (int64), required. Request body required (`UpdateProjectRequest`).

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | The new name for the project |

```bash
MANAGEMENT_TOKEN="YOUR_MANAGEMENT_TOKEN"
PROJECT_ID="12345"

curl -L -X PUT "https://mp.speechmatics.com/v1/projects/${PROJECT_ID}" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Customer support (EU)"}'
```

| Status | Meaning | Body |
|---|---|---|
| 200 | OK | `Project` |
| 404 | Not Found | Empty |

Only `name` can be updated.

Docs: https://docs.speechmatics.com/api-ref/management/update-a-project

### DELETE /projects/{project_id}

Delete a project. Path parameter `project_id`: integer (int64), required.

Deleting a project permanently removes all of its transcripts, usage history, and API keys. The default project cannot be deleted.

```bash
MANAGEMENT_TOKEN="YOUR_MANAGEMENT_TOKEN"
PROJECT_ID="12345"

curl -L -X DELETE "https://mp.speechmatics.com/v1/projects/${PROJECT_ID}" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}"
```

| Status | Meaning | Body |
|---|---|---|
| 204 | Project deleted | Empty |
| 403 | Forbidden. Most probably due to outstanding payments | `ErrorResponse` |
| 404 | Project was not found | `ErrorResponse` |
| 410 | Gone | `ErrorResponse` |
| 500 | Internal Server Error | `ErrorResponse` |

Docs: https://docs.speechmatics.com/api-ref/management/delete-a-project

### GET /api-keys

Get all API keys.

| Query parameter | Type | Required | Description |
|---|---|---|---|
| `project_id` | integer (int64) | No | The `project_id` to filter API keys by |

```bash
MANAGEMENT_TOKEN="YOUR_MANAGEMENT_TOKEN"
PROJECT_ID="12345"

curl -L -X GET "https://mp.speechmatics.com/v1/api-keys?project_id=${PROJECT_ID}" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}"
```

| Status | Meaning | Body |
|---|---|---|
| 200 | OK | Array of `ApiKey` |
| 403 | Forbidden | `ErrorResponse` |
| 404 | Project not found | `ErrorResponse` |
| 410 | Gone | `ErrorResponse` |
| 500 | Internal Server Error | `ErrorResponse` |

The response never includes key values, only metadata.

Docs: https://docs.speechmatics.com/api-ref/management/get-all-api-keys

### POST /api-keys

Create an API key in the workspace. Security: management token or long-lived API key.

Two kinds of key:

- Permanent key: long-lived, for a project. Set `project_id` (and optionally `name`) and omit `ttl`. Needs a management token.
- Temporary key: short-lived, expires automatically. Set `ttl` to the lifetime in seconds. Use temporary keys to authenticate end-user requests without exposing a long-lived key.

| Query parameter | Type | Required | Description |
|---|---|---|---|
| `type` | string enum: `rt`, `batch`, `tts` | No | The product the key can access: `batch` (default), `rt` (Realtime), or `tts` (Text to Speech) |

Request body (`CreateApiKeysRequest`, optional, all fields nullable):

| Field | Type | Constraints | Description |
|---|---|---|---|
| `project_id` | integer (int64) | | The project the API key belongs to. Set this to create a permanent key for a specific project |
| `name` | string | Max 120 characters | A display name for the API key |
| `client_ref` | string | | An end-user reference. For `batch` keys it restricts the key to jobs created with the same `client_ref`; ignored for `rt` keys |
| `ttl` | integer (int64) | 60 to 86400 | Time to live for a temporary key, in seconds (1 minute to 24 hours). Set it to create a temporary key; omit it to create a permanent key |
| `region` | string enum: `eu`, `usa`, `au` | Deprecated | Per the spec, region is now determined by the endpoint called; still accepted for backward compatibility but has no effect |

```bash
MANAGEMENT_TOKEN="YOUR_MANAGEMENT_TOKEN"

curl -L -X POST "https://mp.speechmatics.com/v1/api-keys?type=batch" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 12345, "name": "ci-pipeline"}'
```

| Status | Meaning | Body |
|---|---|---|
| 201 | Created | `CreateApiKeysResponse` (`apikey_id`, `key_value`) |
| 403 | Forbidden, project has maximum number of API keys already | `ErrorResponse` |
| 404 | Not Found | `ErrorResponse` |
| 410 | Gone | `ErrorResponse` |
| 500 | Internal Server Error | `ErrorResponse` |

Store `key_value` immediately. `GET /api-keys` does not return it.

Docs: https://docs.speechmatics.com/api-ref/management/create-an-api-key

### DELETE /api-keys/{apikey_id}

Delete an API key. Path parameter `apikey_id`: string, required. The key stops working immediately.

```bash
MANAGEMENT_TOKEN="YOUR_MANAGEMENT_TOKEN"
APIKEY_ID="APIKEY_ID"

curl -L -X DELETE "https://mp.speechmatics.com/v1/api-keys/${APIKEY_ID}" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}"
```

| Status | Meaning | Body |
|---|---|---|
| 200 | OK | `OkResponse` |
| 404 | Not Found | `ErrorResponse` |
| 410 | Gone | `ErrorResponse` |
| 500 | Internal Server Error | `ErrorResponse` |

Docs: https://docs.speechmatics.com/api-ref/management/delete-an-api-key

## Schemas

### Project

| Field | Type | Notes |
|---|---|---|
| `project_id` | integer (int64) | Required |
| `is_default` | boolean | Nullable |
| `is_active` | boolean | Nullable |
| `name` | string | |
| `description` | string | |
| `created_at` | string (date-time) | |
| `deleted_at` | string (date-time) | |

### ApiKey

| Field | Type | Notes |
|---|---|---|
| `apikey_id` | string | Required |
| `name` | string | |
| `created_at` | string (date-time) | |
| `client_ref` | string | |

### CreateApiKeysResponse

| Field | Type | Notes |
|---|---|---|
| `key_value` | string | Required. The secret key value |
| `apikey_id` | string | Required |

### ErrorResponse

| Field | Type | Notes |
|---|---|---|
| `code` | integer | Required. The HTTP status code |
| `error` | string | Required. The error message |
| `detail` | string | The details of the error |

### OkResponse

| Field | Type | Notes |
|---|---|---|
| `status` | string | The OK string, for example `OK` |

## Temporary keys: which endpoint

The authentication docs (https://docs.speechmatics.com/get-started/authentication) document temporary keys through a separate endpoint authenticated with an API key:

```bash
curl -L -X POST "https://mp.speechmatics.com/v1/jwts?type=rt" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $API_KEY" \
     -d '{"ttl": 60 }'
```

- That page states `POST /v1/jwts` replaces the deprecated `POST /v1/api_keys` endpoint, returns only `key_value`, and accepts `type` values `batch` (default) and `rt`.
- On `/v1/jwts`, `region` (`eu` default, `usa`, `au`) is significant for `batch` keys: the key is valid only in that region.
- Docs versus spec: the authentication page names the deprecated endpoint `POST /v1/api_keys` (underscore) and lists `type` values `batch` and `rt` only. The spec path is `POST /v1/api-keys` (hyphen); it is not marked deprecated, still documents temporary keys through `ttl`, adds `type=tts`, and says `region` has no effect.
- Prefer `/v1/jwts` for temporary keys and `POST /v1/api-keys` with a management token for permanent keys.

Full temporary key guidance is in `speechmatics:get-started`.

## Automation patterns

Provision a tenant:

1. `POST /projects` with a `name`. Read `project_id` from the response.
2. `POST /api-keys` with that `project_id` and a `name`. Store `key_value` in your secret manager and record `apikey_id`.

Rotate a key:

1. `POST /api-keys` for the same `project_id`.
2. Roll out the new `key_value`.
3. `DELETE /api-keys/{apikey_id}` for the old key.

Audit keys:

1. `GET /projects`.
2. For each project, `GET /api-keys?project_id=<project_id>` and review `name` and `created_at`.

Give each automation a token with only the permissions it uses.
