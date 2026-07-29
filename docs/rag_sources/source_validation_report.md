# RAG Source Validation Report

Validation and retrieval date: 2026-07-29

## Summary

- Sources reviewed: 5
- Successfully retrieved as public HTML: 5
- Inaccessible source pages: 0
- Redirected source pages: 0
- Duplicate downloads: 0
- Irrelevant sources: 0
- Approval state: all sources remain `pending_internal_review`

All five source URLs use HTTPS and are hosted on domains that identify themselves as
the official websites of the organisations recorded in the manifest. Page titles,
site branding, and page content were checked against the recorded owner and topic.
No authentication or access-control bypass was attempted.

## Source results

| Source ID | Owner/domain verification | Retrieval | Relevance | Local file | SHA-256 |
|---|---|---|---|---|---|
| `SRC-ACC-001` | `combank.lk`; page branding identifies Commercial Bank of Ceylon | HTTP 200, HTML, no redirect | Page title is “Commercial Bank \| Regular Savings Account”; relevant | `documents/accounts_combank_regular_savings.html` | `036ed052d6a78020d0951d75d165778ad0d310ce01a1788c0d3ee89b58e85315` |
| `SRC-CARD-001` | `combank.lk`; page branding identifies Commercial Bank of Ceylon | HTTP 200, HTML, no redirect | Page title is “Commercial Bank \| Card dispute management policy”; relevant | `documents/cards_combank_dispute_policy.html` | `ad887aa0ed93d915ca9d3bea0b51398c43c8fcdccbd268feecced686d7df782e` |
| `SRC-TRF-001` | `combank.lk`; page branding identifies Commercial Bank of Ceylon | HTTP 200, HTML, no redirect | Page title is “Commercial Bank \| Card to Card Fund Transfer Facility”; relevant | `documents/transfers_combank_card_to_card.html` | `d14f15fd1b21e7da5a2651df41c1eecaa73dd8a1ba34ebe3a1a0eb68b1b6948d` |
| `SRC-LOAN-001` | `peoplesbank.lk`; page branding and canonical URL identify People’s Bank | HTTP 200, HTML, no redirect | Personal-loan page includes the Pahasu scheme; relevant | `documents/loans_peoples_bank_pahasu.html` | `2941770f8da2a12ae6f60948938a5e134e5b92f4e4310d3e5ba62f19df30413e` |
| `SRC-FRAUD-001` | `cbsl.gov.lk`; page branding and canonical URL identify the Central Bank of Sri Lanka | HTTP 200, HTML, no redirect | Page title matches the recorded online-scams warning; relevant | `documents/fraud_cbsl_online_scams.html` | `e79612b73b28c63d812294ef12469e8a1478df6cdc6643d5f71c6be31a9002e7` |

## Access and robots review

- People’s Bank published a `robots.txt` file. The listed source path is not
  disallowed.
- The Central Bank of Sri Lanka published a `robots.txt` file. The listed source
  path is not disallowed, and its 10-second crawl delay was respected.
- Commercial Bank returned HTTP 403 for `/robots.txt`. This made its robots policy
  unavailable for inspection. The three source pages themselves were publicly
  accessible without authentication and returned HTTP 200. Each was downloaded
  once; no attempt was made to bypass the robots response or any access control.

## Exceptions and findings

- Inaccessible sources: none.
- Redirected sources: none.
- Duplicates: none. All downloaded files have distinct SHA-256 checksums.
- Irrelevant sources: none.
- Review note: Commercial Bank’s `robots.txt` was inaccessible as described above.

The manifest did not previously contain a checksum field. A
`checksum_sha256` column was added and populated for every source.
