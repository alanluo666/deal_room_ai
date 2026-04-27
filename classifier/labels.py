"""Document type label vocabulary.

ALIGNMENT WITH BOSTON: this is the public contract for the classifier output.
The API surface (and any UI badges) should reference DOC_TYPES so they stay in
sync. If you add a label, retrain before the API ships it as a valid value.
"""

DOC_TYPES: tuple[str, ...] = (
    "financials",
    "legal",
    "mgmt_presentation",
    "contract",
    "due_diligence_report",
    "email_correspondence",
    "other",
)

LABEL_TO_INDEX: dict[str, int] = {label: i for i, label in enumerate(DOC_TYPES)}
INDEX_TO_LABEL: dict[int, str] = {i: label for i, label in enumerate(DOC_TYPES)}
