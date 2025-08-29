import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Initialize the Streamlit app
st.title("Avalanche Streamlit App")

# Get data from Snowflake
session = st.connection("snowflake").session()
query = """
SELECT
    *
FROM
    REVIEWS_WITH_SENTIMENT
"""
df_reviews = session.sql(query).to_pandas()
df_string = df_reviews.to_string(index=False)

# Convert date columns to datetime
df_reviews['REVIEW_DATE'] = pd.to_datetime(df_reviews['REVIEW_DATE'])
df_reviews['SHIPPING_DATE'] = pd.to_datetime(df_reviews['SHIPPING_DATE'])

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Visualizations", "📁 Data Explorer", "💬 Chatbot"])

# --- Tab 1: Visualizations ---
with tab1:
    st.subheader("Average Sentiment by Product")
    product_sentiment = df_reviews.groupby("PRODUCT")["SENTIMENT_SCORE"].mean().sort_values()

    fig, ax = plt.subplots()
    product_sentiment.plot(kind="barh", ax=ax, title="Average Sentiment by Product")
    ax.set_xlabel("Sentiment Score")
    plt.tight_layout()
    st.pyplot(fig)

# --- Tab 2: Data Explorer ---
with tab2:
    st.subheader("Filter by Product")

    product = st.selectbox("Choose a product", ["All Products"] + list(df_reviews["PRODUCT"].unique()))

    if product != "All Products":
        filtered_data = df_reviews[df_reviews["PRODUCT"] == product]
    else:
        filtered_data = df_reviews

    # Display the filtered data as a table
    st.subheader(f"📁 Reviews for {product}")
    st.dataframe(filtered_data)

    # Visualization: Sentiment Distribution for Selected Products
    st.subheader(f"Sentiment Distribution for {product}")
    fig, ax = plt.subplots()
    filtered_data['SENTIMENT_SCORE'].hist(ax=ax, bins=20)
    ax.set_title("Distribution of Sentiment Scores")
    ax.set_xlabel("Sentiment Score")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)

# --- Tab 3: Chatbot with History ---
with tab3:
    st.subheader("💬 Chat with Your Data")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if user_input := st.chat_input("Ask a question about your data..."):
        # Save user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Use Snowflake Cortex
                    response = session.sql(
                        """
                        SELECT SNOWFLAKE.CORTEX.COMPLETE(
                            'claude-3-5-sonnet',
                            ?
                        )
                        """,
                        params=[f"Answer this question using the dataset:\n\n<context>\n{df_string}\n</context>\n\nQuestion: {user_input}"]
                    ).collect()[0][0]
                except Exception as e:
                    response = f"⚠️ Error: {e}"

                st.markdown(response)

        # Save assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
