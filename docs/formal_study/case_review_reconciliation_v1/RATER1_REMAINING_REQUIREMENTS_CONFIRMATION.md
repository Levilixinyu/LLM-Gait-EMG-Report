# Rater1 confirmation of remaining case requirements

Reviewer: rater1  
Review date: 2026-09-18  
Source: `Case_requirements_reconciliation_consensus.xlsx`  
Source SHA-256: `caffdccafbbb8665481dbf2899c71817e3320ff27caa8afee989134cece769ac`

## Decision and explicit coverage of this confirmation

I have reviewed the current final decisions, final wording and required-component logic for all 177 original rows identified as awaiting rater1 confirmation in `CONSENSUS_RETURN_AUDIT.json`. I accept 176 of these rows as written. The sole exception is **R099 (stroke_Sub29_P, N03)**, for which I request the correction below. This is an explicit confirmation of the 176 listed rows, not an inference from blank response cells or agreement with shared topics.

The accepted identifiers are:

R001, R002, R003, R004, R005, R006, R007, R008, R009, R010, R011, R012, R013, R014, R015, R016, R017, R018, R019, R020, R021, R022, R024, R025, R026, R027, R028, R030, R031, R032, R033, R034, R035, R036, R037, R038, R040, R041, R042, R043, R044, R045, R046, R047, R048, R049, R050, R051, R053, R054, R055, R056, R057, R058, R059, R060, R061, R062, R063, R065, R066, R067, R068, R069, R070, R072, R073, R074, R075, R076, R077, R078, R079, R080, R081, R082, R083, R084, R085, R086, R087, R088, R089, R090, R091, R092, R093, R094, R095, R096, R097, R098, R100, R101, R102, R103, R104, R105, R107, R108, R109, R110, R111, R112, R113, R114, R115, R116, R117, R119, R120, R121, R122, R123, R124, R125, R126, R127, R128, R129, R130, R131, R132, R133, R135, R136, R137, R138, R139, R140, R141, R142, R143, R144, R145, R146, R147, R148, R149, R150, R152, R154, R155, R156, R159, R160, R161, R162, R163, R164, R165, R167, R169, R170, R171, R174, R175, R176, R179, R180, R182, R184, R185, R187, R188, R189, R190, R191, R192, R194, R195, R196, R197, R198, R199, R200.

The accompanying JSON records each accepted row's current final decision, wording and components, together with the source hash. Acceptance is specific to those fields in this workbook version. It does not endorse stale administrative notes as evidence of full consensus.

## Exception: R099

Decision: **Revision required**. Retain the existing `Modify` decision and the two alternative reporting routes.

Reason: The final wording offers a BF signed-deviation route or an RF threshold-extent route, but the following generic sentence and component field require mean-relative direction and approximate cycle location for each route. Those components belong to route A, not route B. This could incorrectly deny full coverage to an otherwise complete RF route. Preserve the agreed OR choice and make the component requirements route-specific.

Complete proposed replacement for final requirement wording (column P):

> Describe EITHER (A) the BF envelope above its phase-specific reference mean at approximately 34% of the analysis cycle OR (B) the RF mean envelope above the algorithm-defined threshold for approximately 95% of the analysis cycle AND spanning the cycle boundary. One complete route is sufficient; both routes are not required. For route A, muscle identity, mean-relative direction and approximate cycle location are jointly required; exact repetition of max |z| 5.1 is optional. For route B, muscle identity, approximate above-threshold coverage and boundary-spanning status are jointly required; exact interval endpoints are optional.

Complete proposed replacement for final required components (column Q):

> OR between routes. Route A requires BF AND above its phase-specific reference mean AND approximately 34% of the analysis cycle. Route B requires RF AND the mean envelope above the algorithm-defined threshold for approximately 95% of the analysis cycle AND spanning the cycle boundary. Exact max |z| 5.1 is optional for route A; interval endpoints 80%-75% are optional for route B. Route B does not require a direction relative to the reference mean or a location of maximum deviation. Apply the approved shared interpretation limits: threshold coverage is not physiological activation duration, continuous contraction or proof of disease; neither route licenses unsupported gait-phase, normal-timing or severity claims.

Input support: the actual model user input supplies BF max |z| 5.1, above reference at 34% of the cycle, and RF above-threshold coverage of 95%, with an 80%-75% interval wrapping the cycle boundary. The correction requires no supplementary-plot information, new calculation or additional clinical inference.

Rater1 accepts the replacement above. Rater2 must confirm this correction before R099 can be recorded as bilaterally finalized. No rater2 acceptance is entered or inferred here. The remaining 176 rows do not need repeated individual signatures.

## Prior confirmations and scope

The previously recorded bilateral responses to the eight shared topics, 23 original requirements and 13 additions remain in place. This confirmation does not withdraw or reopen them. Full confirmation of all original requirements is not yet claimed because R099 remains an exception.

This confirmation concerns prospective case-specific scoring requirements only. It does not change historical reports, ratings or adjudications, authorize report generation, confirm participant exposure, or approve scoring weights, study outcomes, formal samples or statistical analyses. The source consensus workbook, independent review returns and existing audit records have been preserved unchanged.
