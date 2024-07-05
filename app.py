import streamlit as st
from new import user_input
# from evaluate import load  # Uncomment if needed
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

    # Create a form for input and submission
    with st.form(key='question_form', clear_on_submit=True):
        question = st.text_input("Ask a question:")
        submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        with st.spinner("Generating response..."):
            response, context_docs = user_input(question)
            output_text = response.get('output_text', 'No response')  # Extract the 'output_text' from the response
            st.write(output_text)

    # Add some footer
    st.markdown("---")
    st.markdown("**Powered by**: Aryma Labs")

# Main function to run the app
def main():
    create_ui()

if __name__ == "__main__":
    main()
