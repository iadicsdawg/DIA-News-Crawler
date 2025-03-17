# Import required libraries
import streamlit as st
from apify_client import ApifyClient
import re
import pandas as pd
import io

# Set page configuration first
st.set_page_config(
    page_title="Overseas Investment Crawler",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Load password from Streamlit secrets (with error handling)
if "APP_PASSWORD" not in st.secrets:
    st.error("⚠️ Error: APP_PASSWORD is missing from secrets!")
    st.stop()

APP_PASSWORD = st.secrets["APP_PASSWORD"]

# Password-protected login screen
def login():
    st.title("🔒 Password Required")
    password = st.text_input("Enter Password:", type="password")

    if password == APP_PASSWORD:
        st.success("✅ Access Granted!")
        return True
    elif password:
        st.error("❌ Incorrect Password")
        return False
    return False

# Stop execution if login fails
if not login():
    st.stop()

# Ensure API Token exists
if "APIFY_TOKEN" not in st.secrets:
    st.error("⚠️ Error: APIFY_TOKEN is missing from secrets!")
    st.stop()

APIFY_TOKEN = st.secrets["APIFY_TOKEN"]

# Custom CSS styling for UI
st.markdown("""
    <style>
        .main-title {
            color: #007BFF;
            font-size: 2.5em;
            text-align: center;
            padding: 20px;
        }
        .stButton>button, .stDownloadButton>button {
            background-color: #007BFF !important;
            color: white !important;
            font-size: 18px !important;
            font-weight: bold !important;
            padding: 12px !important;
            border-radius: 8px !important;
            width: 100% !important;
            text-align: center !important;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2) !important;
            border: none !important;
            cursor: pointer !important;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            background-color: #0056b3 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Main content
st.markdown('<h1 class="main-title">🌐 DIA Overseas Investment News Crawler</h1>', unsafe_allow_html=True)
st.markdown("**Extract the latest news update of firms!**")

# URL input section
st.write("### 🖇️ Upload File or Enter URLs Manually")
uploaded_file = st.file_uploader("Upload a text or CSV file containing URLs (one per line):", type=["txt", "csv"])

# Read URLs from file if uploaded
uploaded_urls = []
if uploaded_file is not None:
    try:
        file_content = uploaded_file.read().decode("utf-8").strip()
        uploaded_urls = file_content.split("\n")  # Split URLs by new line
    except Exception as e:
        st.error(f"Error reading file: {e}")

# Text input area for manual entry, pre-filling with uploaded URLs
urls = st.text_area(
    "Or enter URLs manually (one per line):",
    value="\n".join(uploaded_urls) if uploaded_urls else "",
    height=150,
    placeholder="Example URLs:\nhttps://www.investment-news.com\nhttps://www.global-capital.com",
    help="Upload a file or manually enter URLs."
)

# URL Validation Function
def validate_urls(url_list):
    url_regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:\S+(?::\S*)?@)?'  # user:pass authentication
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)'  # TLD
        r'(?::\d+)?'  # port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return all(url_regex.match(url.strip()) for url in url_list if url.strip())

# Function to run the Apify actor
def run_apify_actor(urls):
    client = ApifyClient(APIFY_TOKEN)

    run_input = {
        "start_urls": [{"url": url.strip()} for url in urls if url.strip()],
        "extractDetailedInformation": True,
        "maxResults": 50,
    }

    with st.spinner("🚀 Gathering investment insights..."):
        run = client.actor("winning_ics/guides-part-2").call(run_input=run_input)

    dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return dataset_items

# Button for running the crawler
col1, col2, col3 = st.columns([1, 2, 1])  # Centered button layout
with col2:
    if st.button("🚀 Run Crawler"):
        url_list = urls.split('\n')

        if not urls.strip():
            st.error("Please enter at least one URL")
        elif not validate_urls(url_list):
            st.error("Invalid URL format detected. Please check your URLs.")
        else:
            try:
                results = run_apify_actor(url_list)

                if not results:
                    st.warning("No articles found. Try different URLs.")
                else:
                    st.success(f"Found {len(results)} relevant articles!")
                    st.markdown("---")

                    df = pd.DataFrame(results)

                    df = df.rename(columns={
                        "content": "Content",
                        "date": "Date",
                        "overseas_investment_related": "Overseas Investment Related",
                        "supporting_evidence": "Supporting Evidence",
                        "title": "Title",
                        "url": "URL"
                    })

                    st.dataframe(df, use_container_width=True)

                    # Save DataFrame to an Excel file
                    excel_buffer = io.BytesIO()
                    df.to_excel(excel_buffer, index=False, sheet_name="Apify Results")
                    excel_buffer.seek(0)

                    st.markdown("### 📤 Export Results")
                    
                    # Center the download button
                    with col2:
                        st.download_button(
                            label="📥 Download Results as Excel",
                            data=excel_buffer,
                            file_name="Apify_Results.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    st.markdown("### Results")
                    for idx, item in enumerate(results, 1):
                        with st.expander(f"📰 Article #{idx}: {item.get('title', 'Untitled')}"):
                            st.caption(f"**Published**: {item.get('date', 'N/A')}")
                            st.write(f"**Content**: {item.get('content', 'No content available')}")
                            st.write(f"**Overseas Investment Related**: {item.get('overseas_investment_related', 'N/A')}")
                            st.write(f"**Supporting Evidence**: {item.get('supporting_evidence', 'N/A')}")
                            st.markdown(f"[🔗 Read more]({item.get('url', '#')})", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error running crawler: {str(e)}")

# Footer
st.markdown("""
    <div class="footer">
        ℹ️ Results are not stored.
    </div>
""", unsafe_allow_html=True)