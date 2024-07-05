import streamlit as st
from new import user_input
from evaluate import load
# Load the ROUGE metric
import time

def create_ui():
    st.title("LinkedIn GPT!")
    st.sidebar.image("Aryma Labs Logo.jpeg", use_column_width=True)
    st.sidebar.write("### Welcome to Aryma Labs")
    st.sidebar.write("Ask a question below and get instant insights.")

    # Add some instructions
    # st.markdown("### Instructions")
    # st.markdown(
    #     """
    #     1. Enter your question in the text box below.
    #     2. Click on 'Submit' to get the response.
    #     3. View the answer generated based on the cool stuff from Aryma Labs.
    #     """
    # )

    # Get user input
    question = st.text_input("Ask a question:")

    # Call user_input function when user clicks submit
    if st.button("Submit"):
        with st.spinner("Generating response..."):
            # start_time = time.time()
            response , context_docs = user_input(question)
            # end_time = time.time()
            # rouge = evaluate.load('rouge')
            output_text = response.get('output_text', 'No response')  # Extract the 'output_text' from the response
            # context = ' '.join([doc.page_content for doc in context_docs])
            # Ensure predictions and references are lists of strings
            # results = rouge.compute(predictions=[output_text], references=[context])
            # st.success("Response:")
            st.write(output_text)
            # st.success("docs:")
            # st.write(context_docs)

    # Add some footer
    st.markdown("---")
    st.markdown("**Powered by**: Aryma Labs")

# Main function to run the app
def main():
    create_ui()

if __name__ == "__main__":
    main()
