# Order-77 Delivery Timeline (Verifiable Sample)

[2026-02-03T09:00:00Z] user: Order-77 is pending. Payment System is linked with Carrier Alpha for pickup.
[2026-02-03T09:12:00Z] assistant: Carrier Alpha reports pickup delay. Order-77 remains pending.
[2026-02-03T09:25:00Z] user: Correction: pickup completed by Carrier Beta. Payment System updated Order-77 to shipped.

## Key entities
- ORDER-77
- PAYMENT SYSTEM
- CARRIER ALPHA
- CARRIER BETA

## Expected temporal relation
- Initial pending state becomes superseded by shipped state after correction.
- Carrier relationship changes from Alpha plan/delay to Beta completion.
