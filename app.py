"""
Business Discovery Tool — Streamlit UI
Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import io
import time

from models import Business, Recommendation
from engine.recommender import get_recommendations
from scraper.demo_scraper import DemoScraper
from scraper.seek_scraper import SeekBusinessScraper, MAJOR_CITIES

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Business Discovery Tool",
    page_icon="🔍",
    layout="wide",
)

# SEEK Business industry categories
SEEK_CATEGORIES = [
    "All Categories",
    "Food & Drink",
    "Retail",
    "Health, Beauty & Fitness",
    "Cleaning & Maintenance",
    "Accommodation, Tourism & Leisure",
    "Commercial Services",
    "Education, Coaching & Training",
    "Automotive & Marine",
    "Manufacturing, Wholesale & Distribution",
    "Home & Garden",
    "Technology & Internet",
    "Transport & Logistics",
    "Other (type your own)",
]

# ── Sidebar: Scraper Settings ────────────────────────────────
st.sidebar.title("⚙️ Settings")

SCRAPERS = {
    "SEEK Business (AU)": SeekBusinessScraper,
    "Demo (Sample Data)": DemoScraper,
}

platform = st.sidebar.selectbox("Platform", list(SCRAPERS.keys()))

location_options = ["All Major Cities", "All Australia"] + MAJOR_CITIES + ["Custom..."]
location_choice = st.sidebar.selectbox("Location", location_options)

if location_choice == "Custom...":
    location = st.sidebar.text_input("Enter city name", "")
elif location_choice == "All Major Cities":
    location = "all"
elif location_choice == "All Australia":
    location = ""
else:
    location = location_choice

category_choice = st.sidebar.selectbox("Category", SEEK_CATEGORIES)

if category_choice == "Other (type your own)":
    category = st.sidebar.text_input("Enter category keyword", "")
elif category_choice == "All Categories":
    category = ""
else:
    category = category_choice

days_back = st.sidebar.slider("Listings posted within (days)", 1, 30, 7)
max_results = st.sidebar.slider("Max results", 10, 500, 100)

# ── Main Area ────────────────────────────────────────────────
st.title("🔍 Business Discovery Tool")
st.caption("Find acquisition-ready Australian businesses faster.")

# ── Settings Preview ─────────────────────────────────────────
with st.expander("📋 Current Settings", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Platform:** {platform}")
        st.markdown(f"**Location:** {location_choice}")
        st.markdown(f"**Category:** {category_choice if category_choice != 'Other (type your own)' else category or 'Not set'}")
    with col2:
        st.markdown(f"**Listings within:** {days_back} days")
        st.markdown(f"**Max results:** {max_results}")

# ── Step 1: Scrape ───────────────────────────────────────────
st.header("📋 Step 1: Scrape Listings")

if location == "all":
    st.warning("⚠️ Scraping 14 cities — this may take several minutes depending on the platform.")

scrape_label = "🔄 Run Scraper"
if location == "all":
    scrape_label = "🔄 Scrape All Major Cities (14 cities)"

if "scraping" not in st.session_state:
    st.session_state["scraping"] = False

if st.button(scrape_label, type="primary", disabled=st.session_state["scraping"]):
    st.session_state["scraping"] = True
    businesses = []

    if location == "all":
        progress_bar = st.progress(0)
        status_text = st.empty()
        scraper = SCRAPERS[platform]()

        for idx, city in enumerate(MAJOR_CITIES):
            status_text.text(f"Scraping {city}...")
            try:
                city_biz = scraper.scrape(
                    days_back=days_back,
                    location=city,
                    category=category,
                    max_results=max_results // len(MAJOR_CITIES),
                )
                businesses.extend(city_biz)
                status_text.text(f"Scraping {city}... Found {len(city_biz)} listings")
            except Exception as e:
                status_text.text(f"Scraping {city}... Error: {e}")
            progress_bar.progress((idx + 1) / len(MAJOR_CITIES))

        status_text.text(f"✅ Done! Found {len(businesses)} total listings across {len(MAJOR_CITIES)} cities.")
        progress_bar.progress(1.0)
    else:
        with st.spinner(f"Scraping {platform}..."):
            scraper = SCRAPERS[platform]()
            businesses = scraper.scrape(
                days_back=days_back,
                location=location,
                category=category,
                max_results=max_results,
            )
        st.success(f"✅ Found {len(businesses)} listings from the last {days_back} days")

    st.session_state["businesses"] = businesses
    st.session_state["scraping"] = False
    st.rerun()

# ── Status Card ──────────────────────────────────────────────
if "businesses" in st.session_state and st.session_state["businesses"]:
    businesses = st.session_state["businesses"]
    st.divider()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Total Listings Found", len(businesses))
    with col_b:
        unique_cities = len(set(b.location for b in businesses))
        st.metric("Cities Covered", unique_cities)
    with col_c:
        if "recommendations" in st.session_state and st.session_state["recommendations"]:
            best = max(r["overall_score"] for r in st.session_state["recommendations"])
            st.metric("Best Opportunity Score", f"{best}/100")
        else:
            st.metric("Best Opportunity Score", "—")

    # ── Step 2: Review Results ───────────────────────────────
    st.header("📊 Step 2: Review Results")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_cat = st.multiselect(
            "Filter by Category",
            sorted(set(b.category for b in businesses)),
        )
    with col2:
        filter_loc = st.multiselect(
            "Filter by Location",
            sorted(set(b.location for b in businesses)),
        )
    with col3:
        filter_type = st.multiselect(
            "Opportunity Type",
            sorted(set(b.raw_data.get("opportunity_type", "") for b in businesses if b.raw_data.get("opportunity_type"))),
        )
    with col4:
        price_options = [b.raw_data.get("price_min", 0) for b in businesses if b.raw_data.get("price_min", 0) > 0]
        if price_options and min(price_options) < max(price_options):
            min_price, max_price = int(min(price_options)), int(max(price_options))
            price_range = st.slider("Price Range (AUD)", min_price, max_price, (min_price, max_price), step=10000)
        elif price_options:
            st.caption(f"All listings priced at ${int(price_options[0]):,}")
            price_range = None
        else:
            price_range = None

    filtered = businesses
    if filter_cat:
        filtered = [b for b in filtered if b.category in filter_cat]
    if filter_loc:
        filtered = [b for b in filtered if b.location in filter_loc]
    if filter_type:
        filtered = [b for b in filtered if b.raw_data.get("opportunity_type") in filter_type]
    if price_range:
        filtered = [b for b in filtered if b.raw_data.get("price_min", 0) >= price_range[0] and b.raw_data.get("price_min", 0) <= price_range[1]]

    if filtered:
        df = pd.DataFrame([b.to_dict() for b in filtered])
        display_cols = ["name", "category", "location", "price_range", "date_posted"]
        st.dataframe(
            df[[c for c in display_cols if c in df.columns]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Showing {len(filtered)} of {len(businesses)} listings")
    else:
        st.warning("No listings found. Try a broader category or increase listings posted within days.")

    # ── Step 3: AI Recommendations ───────────────────────────
    st.header("🤖 Step 3: AI Recommendations")
    st.caption("The AI analyzes pricing, market saturation, and investment value for each listing")

    # Guided criteria fields
    st.subheader("Your Investment Profile")

    col_guided1, col_guided2 = st.columns(2)
    with col_guided1:
        budget = st.text_input("Investment Budget (AUD)", placeholder="e.g. 200000 or Under $300k")
        pref_location = st.text_input("Preferred Location", placeholder="e.g. Melbourne, Sydney CBD")
        pref_industry = st.text_input("Preferred Industry", placeholder="e.g. Food & Drink, Retail")
    with col_guided2:
        involvement = st.selectbox("Owner Involvement", [
            "Any",
            "Full-time owner-operator",
            "Part-time involvement",
            "Passive / hands-off",
        ])
        risk_tolerance = st.selectbox("Risk Tolerance", [
            "Any",
            "Low — stable, established businesses",
            "Medium — balanced risk/reward",
            "High — high growth potential, higher risk",
        ])
        target_roi = st.text_input("Target ROI / Returns", placeholder="e.g. 20% annual, break-even in 2 years")

    # Recommendation modes
    analysis_mode = st.selectbox("Analysis Focus", [
        "Best Overall Opportunity",
        "Lowest Risk",
        "Highest Growth Potential",
        "Best Under Budget",
        "Owner-Operator Friendly",
        "Passive Investment Potential",
        "Undervalued Businesses",
        "Custom (use my criteria below)",
    ])

    custom_criteria = st.text_area(
        "Additional criteria (optional)",
        placeholder="e.g. 'Must have outdoor seating, prefer businesses with 5+ years of operation'",
        height=80,
    )

    top_n = st.slider("Number of recommendations", 1, 10, 5)

    # Build effective criteria
    mode_descriptions = {
        "Best Overall Opportunity": "Best overall investment opportunity considering price, location, market demand, and risk",
        "Lowest Risk": "Lowest risk businesses — stable, established, proven revenue, in non-saturated markets",
        "Highest Growth Potential": "Highest growth potential — undervalued businesses in expanding markets or emerging areas",
        "Best Under Budget": "Best value businesses priced under the buyer's budget with strong fundamentals",
        "Owner-Operator Friendly": "Best for hands-on owner-operators — manageable workload, good systems, training included",
        "Passive Investment Potential": "Best for passive investors — businesses that can run under management with minimal owner involvement",
        "Undervalued Businesses": "Most undervalued businesses — priced below similar listings in the same category",
    }

    if st.button("🧠 Get Recommendations", type="primary"):
        effective_criteria = mode_descriptions.get(analysis_mode, analysis_mode)
        if custom_criteria.strip():
            effective_criteria += f". Additional: {custom_criteria}"

        structured = {
            "budget": budget,
            "location": pref_location,
            "industry": pref_industry,
            "involvement": involvement if involvement != "Any" else "",
            "risk": risk_tolerance if risk_tolerance != "Any" else "",
            "roi": target_roi,
        }

        if not effective_criteria.strip() and not any(structured.values()):
            st.error("Please fill in your investment profile or select an analysis focus.")
        else:
            # Loading states
            progress_placeholder = st.empty()
            progress_placeholder.text("🔍 Analyzing listings...")
            time.sleep(0.5)
            progress_placeholder.text("💰 Comparing prices across categories...")
            time.sleep(0.5)
            progress_placeholder.text("📊 Scoring opportunities...")
            time.sleep(0.5)
            progress_placeholder.text("🤖 Generating AI recommendations...")

            try:
                recommendations = get_recommendations(
                    businesses=filtered,
                    criteria=effective_criteria,
                    top_n=top_n,
                    structured_criteria=structured,
                )
                st.session_state["recommendations"] = recommendations
                progress_placeholder.empty()
            except Exception as e:
                progress_placeholder.empty()
                st.error(f"AI analysis failed: {e}. Try again or check the API connection.")

    # Display recommendations as structured scorecards
    if "recommendations" in st.session_state and st.session_state["recommendations"]:
        recs = st.session_state["recommendations"]

        st.subheader("🏆 Top Recommendations")

        for i, rec in enumerate(recs):
            biz = rec["business"]
            with st.container(border=True):
                # Header row
                col_header, col_score = st.columns([4, 1])
                with col_header:
                    st.subheader(f"#{i+1} — {biz.name}")
                    st.caption(f"{biz.category} • {biz.location} • {biz.price_range}")
                with col_score:
                    st.metric("Opportunity Score", f"{rec['overall_score']}/100")

                # Scorecard
                score_cols = st.columns(4)
                with score_cols[0]:
                    st.metric("Price Attractiveness", f"{rec['price_score']}/10")
                with score_cols[1]:
                    st.metric("Location Strength", f"{rec['location_score']}/10")
                with score_cols[2]:
                    st.metric("Market Demand", f"{rec['market_score']}/10")
                with score_cols[3]:
                    risk_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(rec["risk_level"], "⚪")
                    st.metric("Risk Level", f"{risk_color} {rec['risk_level']}")

                # Why recommended
                st.markdown(f"**Why this business?** {rec['reasoning']}")

                # Highlights
                if rec.get("highlights"):
                    for h in rec["highlights"]:
                        st.markdown(f"✅ {h}")

                # Risks
                if rec.get("risks"):
                    st.markdown("**Potential Risks:**")
                    for r in rec["risks"]:
                        st.markdown(f"⚠️ {r}")

                # Questions to ask seller
                if rec.get("questions"):
                    with st.expander("💬 Questions to Ask Seller"):
                        for q in rec["questions"]:
                            st.markdown(f"• {q}")

                # Next step
                if rec.get("next_step"):
                    st.info(f"**Suggested Next Step:** {rec['next_step']}")

                # View listing button
                st.link_button("View on SEEK Business →", biz.url)

        # Disclaimer
        st.divider()
        st.caption("⚠️ AI recommendations are for research only. Always perform due diligence before making investment decisions.")

    # ── Step 4: Export ───────────────────────────────────────
    st.header("📥 Step 4: Export Report")

    col_export1, col_export2, col_export3 = st.columns(3)

    with col_export1:
        if filtered:
            csv_buffer = io.StringIO()
            df_export = pd.DataFrame([b.to_dict() for b in filtered])
            df_export.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv_buffer.getvalue(),
                file_name="business_listings.csv",
                mime="text/csv",
            )

    with col_export2:
        if filtered:
            excel_buffer = io.BytesIO()
            df_export = pd.DataFrame([b.to_dict() for b in filtered])
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Listings")
            st.download_button(
                label="📊 Download Excel",
                data=excel_buffer.getvalue(),
                file_name="business_listings.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with col_export3:
        if "recommendations" in st.session_state and st.session_state["recommendations"]:
            recs = st.session_state["recommendations"]
            report_lines = [
                "BUSINESS DISCOVERY REPORT",
                "=" * 50, "",
                f"Total listings analyzed: {len(filtered)}",
                f"Top recommendations: {len(recs)}",
                f"Analysis focus: {analysis_mode}", "",
                "TOP RECOMMENDATIONS:",
                "-" * 50,
            ]
            for i, rec in enumerate(recs):
                biz = rec["business"]
                report_lines.append(f"\n#{i+1} — {biz.name}")
                report_lines.append(f"Opportunity Score: {rec['overall_score']}/100")
                report_lines.append(f"Price Score: {rec['price_score']}/10 | Location: {rec['location_score']}/10 | Market: {rec['market_score']}/10")
                report_lines.append(f"Risk Level: {rec['risk_level']}")
                report_lines.append(f"Category: {biz.category}")
                report_lines.append(f"Location: {biz.location}")
                report_lines.append(f"Price: {biz.price_range}")
                report_lines.append(f"Why: {rec['reasoning']}")
                if rec.get("highlights"):
                    report_lines.append(f"Highlights: {', '.join(rec['highlights'])}")
                if rec.get("risks"):
                    report_lines.append(f"Risks: {', '.join(rec['risks'])}")
                if rec.get("questions"):
                    report_lines.append(f"Questions for seller: {'; '.join(rec['questions'])}")
                if rec.get("next_step"):
                    report_lines.append(f"Next step: {rec['next_step']}")
                report_lines.append(f"URL: {biz.url}")

            st.download_button(
                label="📝 Download AI Report",
                data="\n".join(report_lines),
                file_name="business_ai_report.txt",
                mime="text/plain",
            )

else:
    # Empty state
    st.divider()
    st.header("📊 Step 2: Review Results")
    st.info("Run the scraper above to see results here.")
    st.header("🤖 Step 3: AI Recommendations")
    st.info("Scrape listings first, then get AI-powered recommendations.")
    st.header("📥 Step 4: Export Report")
    st.info("Export options will appear after scraping.")
