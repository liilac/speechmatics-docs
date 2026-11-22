# Billing, plans, and usage

Sources:

- https://docs.speechmatics.com/administration/billing
- https://docs.speechmatics.com/administration/plans
- https://docs.speechmatics.com/administration/usage

Prices and discount rates are not in the docs. For current rates use https://www.speechmatics.com/pricing. Do not quote a price.

## Plans

| Plan | Type | Summary |
|---|---|---|
| Free | Self-serve | Start with a $100 credit grant at no cost. No payment card required. |
| Pro | Self-serve | Pay-as-you-go billing with volume and model training discounts. |
| Enterprise | Contract | Dedicated support and deployment options beyond the cloud. |

## Credits and pay-as-you-go

- Speechmatics bills in credits. One credit is worth one US dollar.
- New sign-ups receive a $100 credit grant.
- Accounts created before 1 August 2026 receive a one-time $25 transition credit.
- On Free, credits are used at no cost.
- On Pro (pay-as-you-go, PAYG), a payment card is kept on file. Usage draws down granted credits first. Once they are used up, further usage is charged to the card on the first of each month for the previous month's usage.
- Charges are calculated to the exact second, based on the per-hour rate for each product type.

## Upgrade to Pro

Add a payment card on the Billing page. Adding a card upgrades a Free plan to Pro.

## Payment card

Managing billing requires the Admin role.

### Add or edit

1. Go to **Billing** in the sidebar under **Workspace**.
2. In the **Payment method** section, click **Add payment card**, or **Edit payment information** if a card exists.
3. Enter the card details.
4. Save.

### Remove

1. In the **Payment method** section, click the delete icon next to the card.
2. Confirm.

Without a payment card, the API keeps working for as long as credits remain. Once credits are used up, add a card again to continue.

## Invoices and payments

The **Payments** section lists each billing period with its usage, cost, and status. Each period covers one month. Any charge for usage beyond granted credits is raised on the first of the following month.

| Status | Meaning |
|---|---|
| Paid | The charge has been settled. |
| Due | The charge is outstanding. |
| Skipped | No charge was raised for the period, for example when usage was fully covered by granted credits. |

To view and download the invoice for a period, click the link icon at the end of its row.

The card and invoices apply to the Pro plan only. Enterprise billing is handled through a contract.

## Discounts (Pro)

Two discounts, which can apply at the same time.

### Model training discount

Enable **Model training** in **Manage workspace** to receive a discount on usage. Model training, also called data logging, lets Speechmatics use anonymized data to improve its models and services. The setting can be changed at any time and applies to future usage only.

### Volume discount

Applies automatically to billable usage above 500 hours per month, for each Speech to Text product type (a combination of processing mode and model, such as Realtime Enhanced).

Example: 800 hours of Realtime Enhanced and 400 hours of Realtime Standard in one month are billed as:

- 500 hours of Realtime Enhanced at the base rate
- 300 hours of Realtime Enhanced at the discounted rate
- 400 hours of Realtime Standard at the base rate

The threshold is per product type, not across the workspace total.

## Enterprise

A contract-based plan for organizations that need dedicated support or deployment options beyond the cloud. Billing is through a contract rather than pay-as-you-go, with no payment card or monthly portal billing.

Includes:

- High-touch support: dedicated customer support, onboarding, and solutions engineering.
- On-prem and on-device deployment. These options are available only on Enterprise.
- The best available discounts and early access to new features.

Enterprise customers may also have access to the EU2 and US2 Batch endpoints, region arrangements set in the contract, and must ask support or their account manager to enable temporary keys.

Contact sales: https://www.speechmatics.com/speak-to-sales

## Usage

### View usage in the portal

Portal usage reporting covers cloud usage only. On-prem deployments report usage differently (`speechmatics:container-deployment`).

1. Go to **Usage** in the sidebar under **Workspace**.
2. Select a time range, such as **7D**, **30D**, or **Custom**.
3. Use the **All projects** dropdown to view usage for a single project or across the workspace.

Usage is shown in two charts, **Realtime** and **Batch**, matching the processing mode of each request. Each chart breaks usage down by model and reports total time used and request count.

### Usage by model

| Mode | Models shown |
|---|---|
| Realtime | Standard, Enhanced, Melia 1, Oak 1 |
| Batch | Standard, Enhanced, Melia 1, Oak 1 |
| Agent STT | Linden 1 |

The Enhanced Medical and agent variants are reported under their underlying model, not as separate lines. For example, Batch usage on Enhanced Medical appears under Enhanced.

### Track usage with the API

Use the Usage API: https://docs.speechmatics.com/api-ref/batch/get-usage-statistics

- It currently reports Batch usage only.
- Temporary keys created with a `client_ref` cannot call it (`HTTP 403 - Forbidden`).
- Endpoint details are in `speechmatics:batch-transcription`.

## Common questions

| Question | Answer |
|---|---|
| Why was there no charge this month? | Status **Skipped**: usage was covered by granted credits. |
| When is the card charged? | On the first of each month, for the previous month's usage beyond granted credits. |
| Can I bill each project separately? | No. Billing belongs to the workspace. Usage can be viewed per project. |
| How do I get Realtime usage programmatically? | The Usage API reports Batch only. Use the portal charts for Realtime. |
| How do I get on-prem? | Enterprise plan only. Contact sales. |
