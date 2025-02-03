# Import required libraries
import streamlit as st
from apify_client import ApifyClient
import re
import os
import pandas as pd
import io

# Set up page configuration
st.set_page_config(
    page_title="Overseas Investment Crawler",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS styling using markdown
st.markdown("""
    <style>
        .main-title {
            color: #007BFF;
            font-size: 2.5em;
            text-align: center;
            padding: 20px;
        }
        .result-section {
            margin: 20px 0;
            padding: 15px;
            border-radius: 10px;
            background-color: #F8F9F9;
        }
        .footer {
            text-align: center;
            padding: 10px;
            color: #666;
        }
        .stButton>button {
        background-color: #007BFF !important;  /* Blue color */
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

        .stButton>button:hover {
            background-color: #0056b3 !important; /* Darker blue on hover */
        }
        
        .stDownloadButton>button {
            background-color: #007BFF !important;  /* Blue color */
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

        .stDownloadButton>button:hover {
            background-color: #0056b3 !important; /* Darker blue on hover */
        }

    </style>
""", unsafe_allow_html=True)

# Initialize Apify client (using Streamlit secrets management)
APIFY_TOKEN = st.secrets["APIFY_TOKEN"]

# Sidebar configuration
# with st.sidebar:
#     st.header("Configuration ⚙️")
#     st.info("Enter your Apify token here if using a custom actor:")
#     custom_token = st.text_input("Apify Token", type="password")
    
#     st.markdown("---")
#     st.subheader("Instructions 📖")
#     st.write("""
#         1. Enter URLs (one per line)
#         2. Click 'Run Crawler'
#         3. View results below
#         """)

# Main content area
st.markdown('<h1 class="main-title">🌐 DIA Overseas Investment News Crawler</h1>', unsafe_allow_html=True)
st.markdown("""
    **Extract the latest news update of firms!**  
    """)

# URL input section
with st.container():
    st.write("### 🖇️ Upload File or Enter URLs Manually")
    
    uploaded_file = st.file_uploader(
        "Upload a text or CSV file containing URLs (one per line):", 
        type=["txt", "csv"], 
        accept_multiple_files=False
    )

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

# Validation function
def validate_urls(url_list):
    url_regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:\S+(?::\S*)?@)?'  # user:pass authentication
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)'  # TLD
        r'(?::\d+)?'  # port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return all(url_regex.match(url.strip()) for url in url_list if url.strip())

# Processing function
def run_apify_actor(urls):
    client = ApifyClient(APIFY_TOKEN)
    
    # Prepare actor input
    run_input = {
    "start_urls": [{"url": url.strip()} for url in urls if url.strip()],  # Fix here
    "extractDetailedInformation": True,
    "maxResults": 50,
    }
    
    # Run the actor (using example actor ID)
    with st.spinner("🚀 Gathering investment insights..."):
        run = client.actor("winning_ics/guides-part-2").call(run_input=run_input)
    
    # Fetch results from default dataset
    dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return dataset_items

# Main processing flow
if st.button("Run Crawler 🚀"):
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

                # Convert results to a Pandas DataFrame
                df = pd.DataFrame(results)

                # Rename columns for better readability
                df = df.rename(columns={
                    "content": "Content",
                    "date": "Date",
                    "overseas_investment_related": "Overseas Investment Related",
                    "supporting_evidence": "Supporting Evidence",
                    "title": "Title",
                    "url": "URL"
                })

                # Display results in an interactive table
                st.dataframe(df, use_container_width=True)

                # Save DataFrame to an Excel file in memory
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False, sheet_name="Apify Results")
                excel_buffer.seek(0)  # Move the pointer to the beginning of the buffer

                st.markdown("### 📤 Export Results")

                # Center the button
                col1, col2, col3 = st.columns([1, 2, 1])  # Centered layout
                with col2:
                    st.download_button(
                        label="📥 Download Results as Excel",
                        data=excel_buffer,
                        file_name="Apify_Results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )


                st.markdown("### Results")
                # Display each article in an expandable format
                for idx, item in enumerate(results, 1):
                    with st.expander(f"📰 Article #{idx}: {item.get('title', 'Untitled')}"):
                        st.caption(f"**Published**: {item.get('date', 'N/A')}")
                        st.write(f"**Content**: {item.get('content', 'No content available')}")
                        st.write(f"**Overseas Investment Related**: {item.get('overseas_investment_related', 'N/A')}")
                        st.write(f"**Supporting Evidence**: {item.get('supporting_evidence', 'N/A')}")
                        st.markdown(f"[🔗 Read more]({item.get('url', '#')})", unsafe_allow_html=True)


        except Exception as e:
            st.error(f"Error running crawler: {str(e)}")

# Footer section
st.markdown("""
    <div class="footer">
        ℹ️ Results are not stored.
    </div>
""", unsafe_allow_html=True)

# Summary of code structure (in comments)
# 1. Imports and configuration
# 2. Custom CSS styling for visual appeal
# 3. Sidebar setup for configuration and instructions
# 4. Main content area with title and input section
# 5. Validation and processing functions
# 6. Main execution flow with error handling
# 7. Result display logic with proper formatting
# 8. Footer section for additional information