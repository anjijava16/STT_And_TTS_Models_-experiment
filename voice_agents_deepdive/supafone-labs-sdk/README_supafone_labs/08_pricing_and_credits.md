# 08 · Pricing & Credits

Labs Cloud uses a **prepaid seconds ledger displayed as minutes**. Standard managed calls
cost **$0.10 per connected minute** and debit the balance **once**. That single call-minute
bundles: hosted agent runtime + standard managed speech & transcription + Supafone
Supervisor guidance + QA + call artifacts.

> Pricing data is exposed publicly: `curl https://api.labs.supafone.ai/v1/pricing`

## Plans

| Plan | Price | Included minutes | Overage | (extra col*) |
| --- | --- | --- | --- | --- |
| Open source | $0 forever | — (bring your own AI keys) | — | SDK, adapters, examples under MIT |
| Cloud PAYG | $0.10/min | 5 free, then $40 / 400-min reload | $0.10/min | No subscription required |
| Developer | $49/mo | 490 | $0.10/min | 0 |
| Growth | $249/mo | 2,500 | $0.10/min | 3 |
| Scale | $999/mo | 10,000 | $0.10/min | 20 |

\*The trailing number in the docs' plan table (0 / 3 / 20) appears to be an included
dedicated/seat count — verify against the live pricing page.

- **Trial:** signup grants **5 free minutes**.
- **Pay-as-you-go reload:** **$40 for 400 minutes**, no subscription needed.

## What a recording costs

Supafone does **not** add a second fee just because a call is recorded. Hosted calls debit
the connected voice-agent runtime from the minute ledger; the recording artifact is
included. Transcription and Supervisor work are measured internally but do **not**
double-debit the customer when included in a managed call.

## Usage meters

| Meter | Unit | Meaning |
| --- | --- | --- |
| `agent_minute` | minute | Connected hosted-agent call time; **debited once** |
| `self_healing` | second | Supervisor + QA work; measured but **included** during managed calls |
| `tts` | spoken second | Managed speech output; measured but included |
| `stt` | audio second | Transcription; measured but included |
| `shared_number_pool` | pooled route | Default shared Supafone number pool |
| `managed_number` | number-month | Dedicated Supafone-managed phone number |
| `premium_number` | number-month | $3/month premium number |

## Balance

```bash
curl https://api.labs.supafone.ai/v1/billing/balance \
  -H "Authorization: Bearer $SUPAFONE_LABS_API_KEY"
```

```json
{
  "plan": "growth",
  "seconds_remaining": 150000,
  "minutes_remaining": 2500,
  "top_up": {
    "credit_pack_minutes": 400,
    "credit_pack_price": 40,
    "managed_rate_per_minute": 0.1,
    "pricing": "/v1/pricing"
  }
}
```

## Hosted Stripe checkout (secret key never leaves server)

```python
checkout = client.labs.billing.checkout(kind="plan", plan_key="growth")
print(checkout["checkout_url"])
```

After payment, poll `client.labs.billing.status(checkout_session_id)`. Use
`client.labs.billing.portal()` for an authenticated Stripe Customer Portal link. Webhook
events are signature-verified and deduplicated before credits/entitlements are granted.

### Stripe grant safety rules

- `plan_key` supports `developer`, `growth`, `scale`.
- **Server-owned plan constants** determine the actual grant — Stripe metadata cannot
  increase or reduce minutes.
- Stripe Prices are checked for active status, USD, exact amount, and monthly-vs-one-time
  before checkout opens.
- One-time credit packs always grant **400 minutes** after a verified **$40** payment.
- `invoice.paid` renewals re-grant subscription minutes.
- Credits land on the account balance if one exists, else the newest active key, else a new
  `sl_live_...` key is issued.

## Number billing

Safe default is the shared pool (free):

```json
{ "default_strategy": "default_pool", "default_pool_price_monthly": 0 }
```

Paid number-month choices:

```json
{ "dedicated_number_price_monthly": 1.5, "premium_number_price_monthly": 3 }
```

> Product flows should make number purchases **explicit**. Do not silently upgrade a
> shared-pool user to a dedicated or premium number.

Premium voice providers, international/toll-free carrier usage, phone numbers, and messaging
may be billed **separately** from the standard managed-call minute. For SDK/MCP callers, the
first paid-number request returns a hosted `checkout_url`; after Stripe reports `paid`,
repeat with the `billing_checkout_session_id`. A retry returns the already-provisioned
number rather than buying another.

## Cost sanity check (worked example)

- 1,000 calls/month × avg 3 min = 3,000 minutes.
- At $0.10/min managed = **$300/month** in call minutes (supervision, STT, TTS, QA, recording
  all included).
- Growth plan ($249/mo) includes 2,500 minutes → 500 overage minutes × $0.10 = $50 → **$299**.
- Roughly break-even between Growth-plus-overage and pure PAYG at this volume; PAYG reloads
  ($40/400 min) are the flexible option below subscription thresholds.

---

*Next: [09_research_paper_summary.md](09_research_paper_summary.md)*
