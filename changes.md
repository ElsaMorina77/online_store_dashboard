# Dashboard Enhancements

**Author:** Shqipe Kurti

## Files Modified
- `app.py`
- `src/cancelled_analysis.py` *(new)*
- `requirements.txt` *(added Plotly)*

## Implemented Features

- Added a new **Cancellation Performance Overview** section.
- Created a separate module (`cancelled_analysis.py`) to keep the original dashboard unchanged.
- Added cancellation KPI cards:
  - Total Sales Orders
  - Cancelled Orders
  - Cancellation Rate
  - Net Sales Revenue
  - Cancelled Revenue
  - Cancelled Revenue Share
- Added interactive Plotly visualisations:
  - Monthly Cancellation Rate
  - Top Products by Cancelled Revenue
  - Countries with Highest Cancellation Rate
- Added an Executive Summary, Key Insight, and Final Recommendation to support business decision-making.

## Notes

- The original sales dashboard was preserved.
- Cancellation analysis uses the original transaction data while applying the same sales-cleaning logic as the main dashboard.
- The enhancement provides additional operational insights without affecting the existing dashboard functionality.