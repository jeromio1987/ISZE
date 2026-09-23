# Billing aggregate definitions

Sources: `01_all_sales_isze_to_distributor.csv`, processed on 20 September 2026; prior workbook `Method` and `Scope` sheets. No raw source records are distributed.

Current L12: July 2025-June 2026. Previous L12: July 2024-June 2025. Records are selected using billing date. Only the mapped distributor scope, numeric material references and positive source values are retained; sales-type CR and RE are excluded. April-June 2026 sales-type coverage is incomplete. Repeated export observations are retained because invoice/line identifiers are not available to prove duplication.

Distributor mapping follows the earlier workbook and is stored in `validation/distributor_code_mapping.json`. Mapping uses the supplied sold-to SAP field, falling back to the alternative sold-to field. ITUK/IUK and UMI/UTI are always separate.

Part numbers are stripped of a spreadsheet-style .0 suffix and left-padded to 10 characters; preserve them as strings. No replacement-chain consolidation is performed. Prices are not exported. The EUR column is aggregated eligible parts billing, not accounting net revenue.

`billing_monthly_distributor_part_202407_202606.csv` has one row per distributor, part and observed billing month. `source_record_count` counts contributing export observations; it is not a count of invoices or independent customers. Missing months are not written as rows. Their absence alone cannot distinguish no purchasing from an upstream completeness issue.

`billing_L12_vs_previous_by_distributor_part.csv` contains every distributor-part combination observed in either period. Zero means no eligible observed purchase in the supplied provisional population for that period, not zero market demand. Month counts are observed billing months.

`part_reference_labels_NOT_ZKK_OR_AIM.csv` supplies a representative description and observed catalogue key. The representative description is the description with the highest eligible two-period sales for that part. No ZKK/AIM membership is inferred. Neither descriptions nor prefixes should replace approved application or classification evidence.

All three tables reconcile to the earlier workbook on both overall period totals, every distributor, and every network part-number total. This is a reproduction check, not finance approval or a check of ZKK/AIM quality.
