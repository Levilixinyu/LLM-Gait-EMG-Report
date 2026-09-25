# Consensus return audit

The two discussion replies and the revised consensus workbook have been received. The merge checks pass, but full rater1 confirmation is still outstanding. A completed decision cell is not sufficient evidence of bilateral approval.

## Verified status

- All eight shared topics have a rater1 response and a rater2 acceptance. The merged topic rules match the rater2 responses.
- Twenty-three of the 200 original rows have explicit responses from both reviewers. Their accepted wording and components are correctly incorporated.
- All 13 addition rows have bilateral responses: three mandatory CCI additions are withdrawn, and ten control-provenance requirements are retained.
- The other 177 original rows carry proposed decisions but no separately recorded rater1 confirmation. The revised consensus workbook accurately acknowledges this limitation.
- No current final-decision cell says Pending discussion. That does not close the confirmation-scope gap.
- Original comparison fields are preserved in all returns. Rater1 reply cells are preserved in the rater2 reply. All four checked workbooks contain English text and no formulas.

The rater1 reply explicitly states: "Blank appended case cells mean not separately reassessed in this targeted discussion reply, not approval." Consequently, neither the agreed topic rules nor the filename `consensus` is treated as blanket approval of the 177 remaining rows.

## Required next action

Ask rater1 to review the current final-decision, wording and component fields for the remaining 177 rows and either confirm them as a set or list exceptions. A single explicit, version-specific confirmation can cover those rows; 177 repeated signatures are unnecessary. Do not request a blanket signature without review. Any new substantive changes must then be accepted by rater2.

Current file: `Case_requirements_reconciliation_consensus.xlsx`

Current SHA-256: `caffdccafbbb8665481dbf2899c71817e3320ff27caa8afee989134cece769ac`

Suggested message:

> Thank you; the eight shared topics, 23 explicitly discussed original rows and all 13 additions have been incorporated and checked. Your targeted reply states that blank case-response cells do not mean approval. Please review the remaining 177 rows in Full comparison in Case_requirements_reconciliation_consensus.xlsx (SHA-256 caffdccafbbb8665481dbf2899c71817e3320ff27caa8afee989134cece769ac). Please either confirm that you accept their current final decisions, wording and component logic as a set, or identify any exceptions by comparison_id and provide corrections. One explicit confirmation covering the identified rows is sufficient after review. This confirms prospective case requirements only; it does not authorize model generation or approve exposure status, outcomes or analysis.

The exact 177 identifiers and source hashes are recorded in [CONSENSUS_RETURN_AUDIT.json](CONSENSUS_RETURN_AUDIT.json). No confirmation has been entered on the reviewer's behalf.

## Provenance and scope

Five model-input hashes recorded in the rater1 reply match the current inputs. The source consensus hash recorded in that reply (`e0fa7842...`) identifies an earlier version and differs from the current revised consensus. The historical hash is retained; byte equivalence between versions is not claimed. The replies retain the earlier worksheet content, but this audit does not claim independent verification of unavailable historical XLSX bytes.

Some topic notes and Read first instructions in the returned files describe earlier pending states. Use the current agreed-rule/final-decision fields and the explicit confirmation-scope statement for current status; preserve the returned files as evidence.

This is an administrative provenance and merge check, not a new clinical adjudication or raw-data audit. No returned workbook, prior manifest, historical rating or model report was modified. Formal requirement freezing and model generation have not been performed. External exposure confirmation and the remaining study-design decisions remain separate.
