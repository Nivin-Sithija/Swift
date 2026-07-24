# Sentiment & Priority Labeling Prompt — Banking Support Tickets

You are labeling customer support tickets for a bank's messaging channel. Each ticket includes a pre-classified **category** and the customer's **text**. Assign two independent labels: **sentiment** and **priority**.

Label every ticket independently. Do not let ticket length, politeness, or question-phrasing alone influence your answer. Apply the underlying logic below rather than looking for exact string matches.

## 1. Sentiment: `Neutral` or `Negative`
This is a binary classification. Genuine positive tone (gratitude, praise, relief) is categorized as **Neutral**.

Label as **Negative** ONLY if one of the following is true:
*   **A. Explicit emotional language:** The text directly expresses frustration, anger, or distress (e.g., "ridiculous", "unacceptable", "terrible", "fed up"). This includes descriptions of repeated failures combined with fatigue ("again and again", "how much longer").
*   **B. Implied violation or unexplained loss:** The customer plainly states that money is missing or that they did not do something the bank claims they did. Examples include a bare denial ("I didn't do that"), confirmed missing money ("where are my funds"), or unfair charges ("I was charged twice").

**CRITICAL EXCEPTION FOR FRAUD REPORTS:**
Standard procedural fraud reports (e.g., "I don't recognize this transaction", "someone used my card") must be labeled **Neutral** unless they also contain explicit emotional language (Rule A). These are factual statements of an account discrepancy, not emotional grievances. The severity of a fraud report is captured by its Priority, not its Sentiment.

**CRITICAL EXCEPTION FOR TECHNICAL FAILURES:**
Standard problem reports (e.g., "My transfer failed", "The app crashed") are **Neutral**. A process failing is not Negative sentiment unless the customer frames it as a violation or uses emotional language. When in doubt between a calm factual report and an implied grievance, default to **Neutral**.

## 2. Priority: `Low`, `Medium`, or `High`
Priority is driven primarily by the **category** of the request. Use the typical priority mapping below as your baseline.

*   **High (Security, fraud, blocked access, money integrity):** `card_payment_not_recognised`, `card_swallowed`, `cash_withdrawal_not_recognised`, `compromised_card`, `direct_debit_payment_not_recognised`, `lost_or_stolen_card`, `lost_or_stolen_phone`, `passcode_forgotten`, `pin_blocked`, `terminate_account`, `transaction_charged_twice`, `unable_to_verify_identity`
*   **Medium (Delays, fees, wrong amounts, failed transactions):** `Refund_not_showing_up`, `balance_not_updated_after_bank_transfer`, `balance_not_updated_after_cheque_or_cash_deposit`, `cancel_transfer`, `card_not_working`, `card_payment_fee_charged`, `card_payment_wrong_exchange_rate`, `cash_withdrawal_charge`, `contactless_not_working`, `declined_card_payment`, `declined_cash_withdrawal`, `declined_transfer`, `exchange_charge`, `extra_charge_on_statement`, `failed_transfer`, `request_refund`, `top_up_by_bank_transfer_charge`, `top_up_by_card_charge`, `top_up_failed`, `transfer_fee_charged`, `transfer_not_received_by_recipient`, `virtual_card_not_working`, `wrong_amount_of_cash_received`, `wrong_exchange_rate_for_cash_withdrawal`
*   **Low (Informational, how-to, setup, routine status checks):** `activate_my_card`, `age_limit`, `apple_pay_or_google_pay`, `atm_support`, `automatic_top_up`, `beneficiary_not_allowed`, `card_about_to_expire`, `card_acceptance`, `card_arrival`, `card_delivery_estimate`, `card_linking`, `change_pin`, `country_support`, `disposable_card_limits`, `edit_personal_details`, `exchange_rate`, `exchange_via_app`, `fiat_currency_support`, `get_disposable_virtual_card`, `get_physical_card`, `getting_spare_card`, `getting_virtual_card`, `order_physical_card`, `pending_card_payment`, `pending_cash_withdrawal`, `pending_top_up`, `pending_transfer`, `receiving_money`, `reverted_card_payment`, `supported_cards_and_currencies`, `top_up_by_cash_or_cheque`, `top_up_limits`, `top_up_reverted`, `topping_up_by_card`, `transfer_into_account`, `transfer_timing`, `verify_my_identity`, `verify_source_of_funds`, `verify_top_up`, `visa_or_mastercard`, `why_verify_identity`

*(If a category is unlisted, use the closest analog).*

**THE URGENCY OVERRIDE RULE:**
Regardless of the baseline category, you MUST escalate the priority to **High** if the ticket contains explicit urgency or security signals.
*   Urgency words: "urgent", "ASAP", "immediately", "right away", "emergency"
*   Security words: "stolen", "fraud", "unauthorized", "locked out", "lost my card", "compromised", "hacked"

## 3. Output Format
Return only a valid JSON object for each ticket:
```json
{"sentiment": "Neutral" | "Negative", "priority": "Low" | "Medium" | "High"}
```
