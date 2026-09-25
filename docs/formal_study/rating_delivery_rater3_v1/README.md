# Third independent expert rating packet

> **Historical source package, superseded for distribution.** Use the [independent expert review template](../independent_expert_review_template_v1/README.md) for a new blank delivery and the [human rater register](../HUMAN_RATER_REGISTER.md) for current submissions. The redundant extracted `rater3/` directory was removed after byte-exact ZIP verification on 2026-09-19. The ZIP and creation records remain for provenance and template reproduction. The verifier automatically uses a temporary extraction. The preparation and delivery instructions below describe the original package checkpoint.

Prepared on 2026-09-19 UTC (2026-09-18 America/Chicago).

Send only **Formal_review_rater3.zip**. The recipient should extract the complete archive and open `rater3/START_HERE.html`. The directory containing this README also has researcher records that are not part of the delivery. No message has been sent by the agent.

The reviewer joins at scoring, with sports medicine expertise as described by the study lead. Qualifications, relevant gait/EMG experience, conflicts and independent completion must be recorded by the reviewer; none is certified or prefilled by the packaging process.

## Contents for the reviewer

- 105 anonymous reports from 25 stroke cases and 10 controls, with the same opaque report IDs as the original packets.
- An independently randomized fixed order, separated by at least two other reports between reports from the same case.
- A blank workbook containing 105 Review rows, 447 case-specific Coverage rows, 105 G03 rows and an empty Issues sheet with dropdowns.
- Exact model input texts, reference cards and EMG/kinematic curves for all 35 cases.
- The unchanged approved rubric, full error definitions, 42 synthetic teaching examples, current scope and rubric approval status.
- A sports medicine orientation, step-by-step completion guide, reviewer-background form and offline report pages linked to the corresponding workbook rows.

The new orientation explains existing rules. It does not add a mandatory finding, cutoff, tolerance or scoring category. Original reports, inputs, requirements and source materials remain unchanged. The workbook changes only the reviewer identifier, reading order and administrative wording about independence among all reviewers; judgments and completion fields are blank.

## Delivery and return

1. Send the ZIP and the message in `MESSAGE_TO_RATER3.md`; do not send the project root, other completed workbooks or this researcher folder.
2. Ask the reviewer to read the orientation, instructions, full rubric, definitions and examples before rating.
3. Return `Independent_ratings_rater3_completed.xlsx` and `Reviewer_background_rater3_completed.md`.
4. Preserve the returned bytes and original judgments before discussion. Pending interpretation decisions may remain documented at independent completion.

This task prepared the packet, not a completed third review, expert signature or final consensus. The existing two-rater lock, consensus and analysis commands have not been relabeled or silently extended. They currently accept rater1/rater2; do not submit a rater3 file under either identity. Specify the analysis role and adapt the import/locking and agreement workflow before examining the third review or combining scores. See `REVIEWER_ADDITION_RECORD.md`.

## Provenance and checks

- `BUILD_RECORD.json`: verified canonical source hashes, packet hashes and archive hash.
- `VALIDATION.json`: workbook, unchanged evidence, navigation, spacing, language and archive checks.
- `private/order_provenance.json`: reproducible ordering seed, not a model identity mapping; excluded from the ZIP.
- `../../../../scripts/build_formal_rater3_delivery.py`: refuses to overwrite a prepared package.
- `../../../../scripts/verify_formal_rater3_delivery.py`: validates without reading completed reviews or model identity keys.

The builder reads only the original blank rater assets, public order metadata and the integrity/requirements manifest. It never reads a model identity key or a completed workbook. The source package and earlier expert files are preserved. Static offline navigation is checked; browser rendering is not claimed as tested.
