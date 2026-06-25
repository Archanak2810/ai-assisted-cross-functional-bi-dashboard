# Solution Architecture

The project follows a cloud-connected Business Intelligence architecture:

1. **Data source layer:** RetailMart tables across Sales, Customers, Marketing, Finance, HR, Operations, Logistics, Inventory, and core dimensions.
2. **Data storage layer:** Neon PostgreSQL for browser-accessible cloud database connectivity. A dataset ZIP mode remains available for local demonstrations.
3. **Processing layer:** Python and Pandas for table loading, type standardisation, duplicate handling, joins, KPI calculation, and fact-table construction.
4. **Analytics layer:** descriptive and diagnostic analysis, RFM segmentation, CLV proxy, profitability, working capital, operational and marketing indicators.
5. **Presentation layer:** Streamlit top tabs, sidebar filters, KPI cards, Plotly charts, management interpretations, and report export.
6. **Decision-support layer:** rule-based AI-assisted insights, which translate thresholds and KPI movement into business-language observations and recommendations.

See the accompanying figure in `assets/figures/solution_architecture.png`.
