# Sentiment & Priority Labeling Prompt — Banking Support Tickets

You are labeling customer support tickets for a bank's chat/messaging channel. Each ticket is a short message from a customer about a banking issue (card problems, transfers, payments, account verification, etc.). For every ticket you are given the **category** (the topic, already classified) and the **text** (what the customer wrote). Your job is to assign two labels: **sentiment** and **priority**.

Label every ticket independently. Do not let ticket length, politeness, or question-phrasing alone influence your answer — judge only on the criteria below.

---

## 1. Sentiment: `Neutral` or `Negative`

This is a **binary** classification. There is no "Positive" option — in this dataset, genuine positive tone (gratitude, praise, relief) occurs in well under 1% of tickets, and treating "not urgent" or "politely phrased" as Positive is a common labeling mistake that must be avoided. If a message reads as calm/friendly/appreciative, label it **Neutral** — do not invent a Positive class for it.

### Label `Neutral` when:
- The message is a plain factual question or statement, with no discernible frustration, distress, or complaint.
- The tone is calm, even if the topic itself is about a problem (e.g. "My card isn't working, how do I fix it?" is Neutral — it's a plain report, not an expression of frustration).
- The customer is polite, thankful, or upbeat. (Do not create a separate Positive label — this is still Neutral.)

### Label `Negative` when:
- The text contains explicit frustration/anger/distress language: e.g. "ridiculous", "unacceptable", "terrible", "worst", "angry", "frustrated", "disappointed", "not happy", "furious", "fed up", "sick of", "disgusted", "outraged", "useless", "nightmare", "pathetic", "cheated".
- The customer describes repeated failed attempts or being ignored: "again and again", "over and over", "this is the second/third time", "no one has helped me", "I keep waiting".
- The customer expresses unmet expectations with fatigue/impatience: "still hasn't arrived", "still haven't received", "still don't have", "never received", "how much longer".
- There are 2+ exclamation marks, or ALL CAPS used for emphasis, combined with any negative-leaning content.
- The message expresses fear, panic, or being victimized (fraud, theft, money missing) even without profanity — e.g. "I think someone stole my money, please help immediately!" is Negative, not just because it's urgent but because of the distress expressed.

### Calibration examples (from real labeling errors we found and corrected):
| Text | Correct label | Why |
|---|---|---|
| "How do I top up using Google Pay?" | Neutral | Plain factual question, no emotion |
| "What is the exchange fee?" | Neutral | Plain factual question |
| "I tried my PIN too many times and now my card won't work!" | Neutral (borderline) — only Negative if frustration language accompanies it, not just a factual statement of what happened | A statement of fact with an exclamation mark is not automatically negative — look for actual frustration wording |
| "I still haven't received my card after two weeks, is it lost?" | Negative | "still haven't" + fatigue framing |
| "Why is this taking so long?! I've called three times and no one helps." | Negative | Explicit frustration + repeated-contact fatigue |
| "Thanks so much for sorting that out so quickly!" | Neutral | Positive/grateful tone still maps to Neutral, not a separate class |

**Common mistake to avoid**: do not label something Negative just because the topic is inherently unpleasant (a scam, a lost card, a fee) — label based on the *customer's expressed tone*, not the topic. A calmly-worded report of a serious problem is still Neutral.

---

## 2. Priority: `Low`, `Medium`, or `High`

Priority in this domain is driven **primarily by the category/topic** of the request, not by how the customer phrases it. Categories cluster very consistently around one priority level (in the reference dataset, the average category is ~97% consistent in its priority label). Use the category priority table below as your primary signal.

**Override rule**: regardless of the category's usual priority, if the ticket text contains an explicit urgency/security signal, escalate priority to at least `High`:
- Urgency words: "urgent", "ASAP", "immediately", "right away", "emergency"
- Security/fraud words: "stolen", "fraud", "unauthorized", "locked out", "can't access", "lost my card", "lost my phone", "compromised", "hacked"

This override matters because a category can be *usually* low-stakes (e.g. `card_delivery_estimate` is normally Low) but an individual ticket can still be genuinely urgent ("I need my card ASAP!" should be High even though most `card_delivery_estimate` tickets are Low). Don't let the category prior blind you to explicit urgency in the actual text.

### Category → typical priority (reference table, use as your prior)
**High** (security, fraud, blocked access, money integrity — always High regardless of wording):
`card_payment_not_recognised`, `card_swallowed`, `cash_withdrawal_not_recognised`, `compromised_card`, `direct_debit_payment_not_recognised`, `lost_or_stolen_card`, `lost_or_stolen_phone`, `passcode_forgotten`, `pin_blocked`, `terminate_account`, `transaction_charged_twice`, `unable_to_verify_identity`

**Medium** (delays, fees, wrong amounts, failed/reverted transactions — inconvenient but not blocking):
`Refund_not_showing_up`, `balance_not_updated_after_bank_transfer`, `balance_not_updated_after_cheque_or_cash_deposit`, `cancel_transfer`, `card_not_working`, `card_payment_fee_charged`, `card_payment_wrong_exchange_rate`, `cash_withdrawal_charge`, `contactless_not_working`, `declined_card_payment`, `declined_cash_withdrawal`, `declined_transfer`, `exchange_charge`, `extra_charge_on_statement`, `failed_transfer`, `request_refund`, `top_up_by_bank_transfer_charge`, `top_up_by_card_charge`, `top_up_failed`, `transfer_fee_charged`, `transfer_not_received_by_recipient`, `virtual_card_not_working`, `wrong_amount_of_cash_received`, `wrong_exchange_rate_for_cash_withdrawal`

**Low** (informational, how-to, setup, routine status checks — everything else):
`activate_my_card`, `age_limit`, `apple_pay_or_google_pay`, `atm_support`, `automatic_top_up`, `beneficiary_not_allowed`, `card_about_to_expire`, `card_acceptance`, `card_arrival`, `card_delivery_estimate`, `card_linking`, `change_pin`, `country_support`, `disposable_card_limits`, `edit_personal_details`, `exchange_rate`, `exchange_via_app`, `fiat_currency_support`, `get_disposable_virtual_card`, `get_physical_card`, `getting_spare_card`, `getting_virtual_card`, `order_physical_card`, `pending_card_payment`, `pending_cash_withdrawal`, `pending_top_up`, `pending_transfer`, `receiving_money`, `reverted_card_payment`, `supported_cards_and_currencies`, `top_up_by_cash_or_cheque`, `top_up_limits`, `top_up_reverted`, `topping_up_by_card`, `transfer_into_account`, `transfer_timing`, `verify_my_identity`, `verify_source_of_funds`, `verify_top_up`, `visa_or_mastercard`, `why_verify_identity`

*(If a category isn't listed above, use your judgement based on the closest analog, then apply the urgency override rule regardless.)*

### Calibration examples:
| Text | Category | Correct priority | Why |
|---|---|---|---|
| "I need my card ASAP!" | card_delivery_estimate | High | Urgency override — category is normally Low, but explicit "ASAP" escalates this one ticket |
| "How do I link my card in the app?" | card_linking | Low | Routine how-to, category default applies |
| "Someone made a payment I don't recognize on my account." | card_payment_not_recognised | High | Category is always High (potential fraud), regardless of calm wording |
| "My transfer has been pending for an hour, when will it clear?" | pending_transfer | Low | Category default — a delay question, not urgent language |
| "This is an emergency, please cancel my transfer right now, I sent it to the wrong account!" | cancel_transfer | High | Urgency override — category is normally Medium, "emergency" + "right now" escalates it |

---

## 3. Output format

For each ticket, return:
```json
{"sentiment": "Neutral" | "Negative", "priority": "Low" | "Medium" | "High"}
```

Label sentiment and priority independently — a Neutral-toned message can still be High priority (e.g. a calmly-worded fraud report), and a Negative-toned message can still be Low priority (e.g. an annoyed but routine "why is this so slow" about a Low-priority category with no urgency override).
