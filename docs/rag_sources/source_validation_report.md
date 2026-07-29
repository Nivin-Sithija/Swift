# RAG Source Validation Report

Processing date: 2026-07-29

## Summary

- Sources processed: 5
- Valid cleaned documents: 5
- Rejected cleaned documents: 0
- Minimum meaningful-word requirement: 100
- Approval status: all sources remain `pending_internal_review`

## Validation results

| Source ID | Detected title | Raw words | Main words | Cleaned words | Removed tags | Removed words | Repeated links removed | SHA-256 | Result |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| `SRC-ACC-001` | Commercial Bank \| Regular Savings Account | 2338 | 522 | 547 | 1937 | 1816 | 0 | `036ed052d6a78020d0951d75d165778ad0d310ce01a1788c0d3ee89b58e85315` | **VALID** — passed content validation |
| `SRC-CARD-001` | Commercial Bank \| Card dispute management policy | 3412 | 1788 | 1808 | 1773 | 1624 | 0 | `ad887aa0ed93d915ca9d3bea0b51398c43c8fcdccbd268feecced686d7df782e` | **VALID** — passed content validation |
| `SRC-TRF-001` | Commercial Bank \| Card to Card Fund Transfer Facility | 2502 | 675 | 691 | 1934 | 1827 | 0 | `d14f15fd1b21e7da5a2651df41c1eecaa73dd8a1ba34ebe3a1a0eb68b1b6948d` | **VALID** — passed content validation |
| `SRC-LOAN-001` | Best Personal Loan Rates Sri Lanka: Lowest Interests with Flexible Repayment Plans: People's Bank | 1807 | 111 | 120 | 892 | 1696 | 0 | `2941770f8da2a12ae6f60948938a5e134e5b92f4e4310d3e5ba62f19df30413e` | **VALID** — passed content validation |
| `SRC-FRAUD-001` | Beware of Online Scams - Protect Your Bank Passwords and PINs \| Central Bank of Sri Lanka | 1000 | 392 | 392 | 813 | 608 | 0 | `e79612b73b28c63d812294ef12469e8a1478df6cdc6643d5f71c6be31a9002e7` | **VALID** — passed content validation |

## Method

The cleaner removes scripts, styles, navigation, headers, footers, forms, menus, cookie/consent elements, embedded content, and repeated links. It then selects the source-specific product or article container and retains headings, paragraphs, lists, useful links, and tables.

A cleaned document is rejected when it contains fewer than 100 meaningful words or when navigation-term density indicates that the output is mostly navigation. Rejected content is not written to the cleaned directory or recorded as a cleaned manifest path.
