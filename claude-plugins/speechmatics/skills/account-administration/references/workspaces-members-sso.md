# Accounts, workspaces, members, domain verification, and SSO

Sources:

- https://docs.speechmatics.com/administration/accounts
- https://docs.speechmatics.com/administration/workspaces-concepts
- https://docs.speechmatics.com/administration/manage-members
- https://docs.speechmatics.com/administration/domain-verification
- https://docs.speechmatics.com/administration/sso

## Accounts

An account is an individual identity on the Speechmatics platform. Accounts belong to one or more workspaces, as either Admin or Member.

### Sign up and verification

1. Go to https://portal.speechmatics.com/signup.
2. Sign up with email and password, or with a supported OAuth provider (Google or GitHub).
3. If you signed up with email, verify the address using the link sent to your inbox.

If the email address matches a verified domain, the account joins that workspace automatically. Otherwise a new workspace is created.

### Sign-in methods

- Email and password, or a connected OAuth account (Google or GitHub).
- Manage connected accounts under **Settings > Profile > User** (https://portal.speechmatics.com/settings/profile/user).
- The workspace determines the available sign-in methods. If the workspace has SSO enabled, sign in through the identity provider instead.

### Profile and security

**Settings > Profile** in the portal:

- **User**: update your name, view your email address, manage connected OAuth accounts.
- **Security**: change your password and manage multi-factor authentication (MFA).
- **Signed-in devices**: view active sessions and sign out of individual devices or all other devices at once.

### Delete an account

Deletion is permanent. The same email address cannot be used to create an account again.

1. Go to **Settings > Profile > User**.
2. In the **Delete account** section, click **Delete account**.
3. Confirm.

An account cannot be deleted while it is an Admin in multiple workspaces. Transfer Admin access to another member first, or contact support@speechmatics.com.

## Workspaces

A workspace is the top-level container for a team's use of Speechmatics. Everything done in the portal and API happens within one workspace at a time.

A workspace groups:

- Members: users who can sign in, each with a role.
- Projects: organizational units. API keys are created within projects, and usage can be viewed per project.
- API keys and management tokens: API keys are scoped to a project; management tokens are scoped to the workspace.
- Billing and usage: pricing plan, payment method, credits, invoices, and aggregated usage.

### Switch workspaces

A user can belong to more than one workspace. Each is independent: switching changes which members, projects, keys, and billing details are visible. Open the avatar menu in the portal sidebar and select a workspace.

### Roles

| Role | Capabilities |
|---|---|
| Admin | Full access to the workspace, including settings, billing, members, and projects. Can invite and remove members, create and delete projects and API keys, and rename the workspace. |
| Member | Access to all workspace resources, including projects and usage. Cannot manage members, billing, or workspace settings. |

### Workspaces and authentication

Speechmatics uses WorkOS AuthKit (https://workos.com/docs/authkit) for identity and access. A workspace corresponds to a WorkOS Organization, and the Admin and Member roles correspond to the WorkOS organization roles `admin` and `member`. Sign-in methods, including OAuth and SSO, are configured per workspace.

### Workspaces and regions

A workspace is not tied to a region. The region selected determines which endpoint processes a request, not where the workspace lives. Members of the same workspace can submit work to different regions.

## Manage members

Requires the Admin role.

### Invite a user

1. Go to **Manage workspace** in the sidebar under **Workspace**.
2. In the **Users** section, click **Invite user**.
3. Enter the user's email address.
4. Select a role: **Admin** or **Member**.
5. Click **Invite**.

The user receives an email with a link to complete their account. Until they accept, they do not appear as an active member.

### Change a role

1. In the **Users** table, open the options menu next to the user.
2. Select **Edit role**.
3. Choose the new role and confirm.

### Remove a user

Removal revokes the user's workspace access immediately. API keys they created stay in the workspace and keep working, because keys belong to the workspace rather than the user. Revoke those separately if needed.

1. In the **Users** table, open the options menu next to the user.
2. Select **Remove user**.
3. Confirm.

## Domain verification

Once a domain is verified, anyone signing up with an email address on that domain is added to the workspace as a Member. Requires the Admin role.

### Verify a domain

1. Go to **Manage workspace** in the sidebar under **Workspace**.
2. In the **Domain** section, click **Add domain**.
3. Enter the domain.
4. Add the DNS TXT record shown to the domain's DNS settings.
5. Return to the portal and click **Verify**.

DNS propagation can take up to 24 hours. The status changes to **Verified** once the record is detected.

### Remove a verified domain

1. In the **Domain** section, click the delete icon next to the verified domain.
2. Confirm.

Removing a domain stops new automatic joins. Existing members keep their access.

## Single sign-on (SSO)

SSO lets users sign in with an existing identity provider, such as Okta, Azure AD, or Google Workspace. Authentication is delegated to the provider; Speechmatics does not store passwords for SSO users.

- SSO is an add-on service with a separate subscription. To enable it, contact support@speechmatics.com.
- Supported protocols, through WorkOS AuthKit (https://workos.com/docs/sso): SAML 2.0 and OpenID Connect (OIDC).
- Once support enables SSO for the workspace, follow the provider-specific setup instructions to exchange metadata between the identity provider and Speechmatics.
- Configuration requires the Admin role.
- Verify the domain so SSO users join the workspace automatically, then assign roles under **Manage workspace**.

## Common questions

| Question | Answer |
|---|---|
| How do I onboard a whole company? | Verify the domain so sign-ups join as Members automatically; add SSO through support if required. |
| A colleague left. What do I do? | Remove the user, then revoke any API keys they created if those should stop working. |
| Can a Member create API keys? | The docs say Members can access all workspace resources including projects, and cannot manage members, billing, or workspace settings. They list creating and deleting projects and API keys under Admin. Confirm in the portal. |
| Can one person be in two workspaces? | Yes. Switch with the avatar menu. |
