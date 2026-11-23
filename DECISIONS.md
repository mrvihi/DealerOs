# DealerOS - Technical Decisions



This document records the important technical decisions made during the development of DealerOS.



## 1. Preserve Original CSV Data



Source values are retained during import so that malformed or inconsistent input can be inspected instead of silently discarded.



## 2. Idempotent CSV Import



Source row numbers are used to identify imported rows. Re-running the import updates existing rows instead of creating duplicate records.



## 3. Normalize Record References



Record references are normalized by removing spaces and punctuation and converting them to uppercase. Numeric-only references are given the `REC` prefix to support matching.



## 4. Use Decimal for Financial Values



Financial values are parsed and compared using Python's Decimal type to avoid floating-point precision issues. Commas in numeric strings are handled during parsing.



## 5. Compare Against System A Total Value



System B values are compared with System A's `total\_value`, rather than only its `base\_value`.



## 6. Handle Split Entries



Multiple System B entries can represent a valid split when their combined value matches the corresponding System A total. Repeated identical amounts are treated as duplicates.



## 7. Treat Blank Values as Unknown



Blank System B values are not automatically converted to zero because an empty value does not necessarily mean a zero-value transaction.



## 8. Use Location Mapping for Tenant Isolation



The `locations.csv` file provides the mapping between locations and organizations. Cross-tenant disagreement responses redact opposing-system details to prevent exposing another organization's record information.



## 9. Retain VOIDED Records



VOIDED records are retained in the imported data. Matching System B entries are flagged separately instead of being treated as ordinary financial mismatches.



## 10. Document Current Security Limitations



The current API filters records using the supplied `org\_id` parameter. Authentication and server-enforced tenant authorization are not implemented, so the application is not intended for production use.




