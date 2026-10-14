# PayFast ITN → n8n webhook (future addition)

The Donate form on `/contribute/` (and `/af/contribute/`) posts to Payfast's
classic hosted payment page (`https://www.payfast.co.za/eng/process`). Today
`notify_url` points at the site homepage, so **nobody verifies or records
payments server-side** — confirmations exist only as Payfast transaction
emails and on the Payfast dashboard. This doc describes adding an n8n webhook
as the `notify_url` so every payment is confirmed and logged, using the same
pattern as the contact-form webhook (`https://primary-production-ff69.up.railway.app/webhook/saawe-contact`).

## What Payfast sends

When a payment finishes, Payfast server-to-server POSTs (form-urlencoded) to
`notify_url`, *before* returning the donor's browser to `return_url`. Key fields:

| Field | Notes |
|---|---|
| `payment_status` | `COMPLETE`, `CANCELLED`, `FAILED` |
| `pf_payment_id` | unique ID of the transaction in Payfast |
| `amount_gross` | total paid (ZAR) |
| `amount_fee` / `amount_net` | fees / What actually credited |
| `name_first`, `name_last`, `email_address` | donor details from the form |
| `item_name` | the "Reference" the donor typed |
| `custom_str1`…`custom_str5` | free pass-through fields (useful for tagging, e.g. page language) |
| `signature` | MD5 integrity hash |

The endpoint must return **HTTP 200**; otherwise Payfast retries at
increasing intervals. (Local testing needs a public URL — n8n on Railway
already is one.)

## Proposed n8n workflow

Webhook node (POST, respond 200 immediately) → Code node (verify) → filter →
action (log / notify / write to sheet).

Verification, in order (all steps are in the Payfast docs' sample `notify.php`):

1. **Signature check** (required). Remove `signature` from the payload,
   concatenate the remaining non-blank fields in payload order as
   `k=value&k2=value2`, URL-encode each value (uppercase, spaces as `+`),
   append `&passphrase=<SECURITY_KEY>` (the passphrase/security key set in
   the Payfast account settings — *not* the merchant key), MD5 it, and
   compare with the received `signature`. n8n: `crypto.createHash('md5')`.
2. **merchant_id matches** `10579164` (guards webhook-only attackers).
3. **Amount check**: if you ever pre-set an amount server-side, confirm
   `amount_gross` equals the expected value. Not applicable today (donor
   chooses the amount, so any `amount_gross > 0` is valid).
4. Optional hardening (Payfast-recommended): compare the request source IP
   against Payfast's published IP ranges, or re-submit the payload to
   `https://www.payfast.co.za/eng/query/validate` and require
   `VALID` in the response.

Only accept `payment_status === 'COMPLETE'` for the success path; log others
for troubleshooting.

## Suggested next actions in the workflow

- Log the transaction (row per payment: pf_payment_id, amount_net, email,
  name, item_name/reference, date, language tag from `custom_str1`).
- Optionally email an internal notification, same spirit as the contact-form flow.
- Store the passphrase as an n8n credential/env var, never in the workflow JSON.

## Checklist when implementing

- [ ] Set a passphrase (security key) in the Payfast merchant portal and note it.
- [ ] Add the `/webhook/saawe-itn` (or similar) webhook in n8n; test with the
      sandbox host `https://sandbox.payfast.co.za/eng/process` and the sandbox
      `merchant_id=10000100, merchant_key=46f0cd694581a` first — point
      `notify_url` at the n8n URL in a test copy of the form.
- [ ] Flip `notify_url` from `https://www.saawe.org.za/` to the real webhook
      URL in `contribute/index.html` and `af/contribute/index.html`
      (that is the only line that changes on this site).
- [ ] Make one real small donation, confirm: webhook received, signature
      verified, HTTP 200 returned, donor still lands back on the site.
- [ ] If `notify_url` keeps failing the signature check with no passphrase:
      once a passphrase is set in the portal, Payfast signs *all* notifications
      with it — old flows without the passphrase check must be updated together.

Note: adding `custom_str1` (e.g. `value="en"` / `value="af"`) is a free
one-line addition to each form if language tagging is wanted later.

Sources: https://developers.payfast.co.za/docs (ITN / notification reference,
signature generation, hosted-page form integration).