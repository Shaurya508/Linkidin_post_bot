import streamlit as st
from new import user_input
from evaluate import load
import time

# Load the ROUGE metric


def create_ui():
    st.title("Linkidin GPT!")
    st.sidebar.image("Aryma Labs Logo.jpeg", use_column_width=True)
    st.sidebar.write("### Welcome to Aryma Labs")
    st.sidebar.write("Ask a question below and get instant insights.")

    # Get user input
    question = st.text_input("Ask a question:")

    # Call user_input function when user presses Enter or clicks Submit
    if st.button("Submit") or st.session_state.enter_pressed:
        with st.spinner("Generating response..."):
            response, context_docs = user_input(question)
            output_text = response.get('output_text', 'No response')  # Extract the 'output_text' from the response
            st.write(output_text)

    # Listen for Enter key press
    if st.session_state.enter_pressed is None:
        st.session_state.enter_pressed = False

    if st.session_state.enter_pressed:
        st.session_state.enter_pressed = False
        with st.spinner("Generating response..."):
            response, context_docs = user_input(question)
            output_text = response.get('output_text', 'No response')  # Extract the 'output_text' from the response
            st.write(output_text)

    st.markdown("---")
    st.markdown("**Powered by**: Aryma Labs")

# Main function to run the app
def main():
    create_ui()

if __name__ == "__main__":
    main()
