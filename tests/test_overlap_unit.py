from datetime import date

import pytest

from app.repositories.availability import ranges_overlap_inclusive

EXISTING_START = date(2026, 11, 11)
EXISTING_END = date(2026, 11, 16)


@pytest.mark.parametrize(
    "new_start,new_end,expected_overlap,case_label",
    [
        (date(2026, 11, 8), date(2026, 11, 10), False, "Before, no touch"),
        (date(2026, 11, 17), date(2026, 11, 20), False, "After, no touch"),
        (date(2026, 11, 12), date(2026, 11, 14), True, "Fully inside"),
        (date(2026, 11, 9), date(2026, 11, 11), True, "Touches only start boundary"),
        (date(2026, 11, 16), date(2026, 11, 18), True, "Touches only end boundary"),
        (date(2026, 11, 10), date(2026, 11, 17), True, "Fully contains existing"),
    ],
)
def test_inclusive_overlap_reference_table(new_start, new_end, expected_overlap, case_label):
    assert (
        ranges_overlap_inclusive(new_start, new_end, EXISTING_START, EXISTING_END)
        is expected_overlap
    ), f"Failed case: {case_label}"
