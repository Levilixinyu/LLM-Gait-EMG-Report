"""EMG preprocessing provenance, independent of the deviation reference."""
RELEASED_COHORT_EMG = "van_criekinge_2023_shared_peak_then_ensemble_mean"
RAW_PIPELINE_EMG = "project_raw_envelope_ensemble_mean_then_peak"
CANDIDATE_PROMPT_VERSION = "limited-evidence-v3.1-candidate"


def normalization_description(processing: str | None, group: str | None = None) -> str:
    if processing == RELEASED_COHORT_EMG:
        qualification = ""
        if group == "stroke":
            qualification = (
                " In the checked stroke release, the denominator is participant-, "
                "side-, and muscle-specific; it is not shared between sides. The "
                "local array audit verified 614 evaluable combinations, not all 700; "
                "86 lacked valid nonzero paired samples."
            )
        elif group == "control":
            qualification = (
                " For healthy controls, the normalization and left/right stride "
                "pooling account comes from the release documentation. Healthy MAT "
                "aggregation and side-specific denominators were not numerically "
                "verified by the stroke audit."
            )
        return (
            "The released EMG curves are ensemble-averaged envelopes. For each "
            "participant and recorded muscle, normalization uses a shared maximum "
            "across the available strides before averaging; individual strides are "
            "not independently rescaled to their own peaks. This pipeline uses the "
            "released mean curves without further amplitude normalization."
        ) + qualification
    if processing == RAW_PIPELINE_EMG:
        return (
            "This project's raw-signal path extracts envelopes, time-normalizes "
            "the available cycles, averages them, and then divides each muscle's "
            "mean envelope by that mean envelope's own peak. This differs from "
            "the preprocessing of the released cohort Excel curves."
        )
    return (
        "Preprocessed EMG curves were supplied, but their amplitude normalization "
        "denominator and averaging order were not specified. Do not infer the "
        "processing method from reference-cohort membership."
    )


EMG_INTERPRETATION_LIMIT = (
    "Amplitudes are relative envelope values, not absolute neural activation, "
    "force, or strength. Do not rank muscles as stronger or weaker from these "
    "amplitudes, or infer stride-to-stride variability from an average curve."
)


def cycle_boundary_description(processing: str | None, group: str, side: str | None) -> str:
    """Documented release event anchor; never infer one from reference membership."""
    if processing != RELEASED_COHORT_EMG:
        return "The cycle-defining event is not established for this input; use cycle percentages only."
    if group == "stroke" and side in ("paretic", "non-paretic"):
        return (
            f"The released {side}-side cycle runs from initial contact of that limb "
            "at 0% to its next initial contact at 100%. The cycle boundary may be "
            "called initial contact; the endpoints are successive occurrences, not "
            "one instant. No intermediate event or phase boundary is supplied."
        )
    if group == "control":
        return (
            "The release dictionary defines contributing strides from initial contact "
            "of the stride-defining limb (0%) to its next initial contact (100%). The "
            "healthy Excel release averages left- and right-side strides, so this is "
            "an initial-contact-aligned pooled cycle, not one named limb's observed "
            "event trace. This event anchor is documentary; healthy MAT pooling was "
            "not numerically reverified. The boundary may be called initial contact "
            "of contributing strides. No intermediate event or phase boundary is supplied."
        )
    return "The cycle-defining limb is unspecified for this input; use cycle percentages only."
