# app.py
import gradio as gr
import time
import os
import io
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd # Import pandas here for use in app.py for live logs display

# Import managers from other modules
from firebase_handler import db # Firestore client
from auth_handler import auth_manager # Auth logic
from email_sender import email_manager # Email sending logic
from excel_handler import excel_manager # Excel processing logic

# Load environment variables (for local development)
load_dotenv()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Global variables for application state
current_send_job = {"running": False, "interrupt": False}
email_logs = [] # To store logs for the current session/send operation
global_user_id = None # Stores the authenticated user's UID
global_user_email = None # Stores the authenticated user's email
global_initial_df = None # Stores the initial DataFrame for final Excel generation

# --- Authentication UI and Logic ---
def login_ui_logic(email, password):
    global global_user_id, global_user_email
    uid, user_email, error = auth_manager.login_user(email, password)

    if error:
        return f"Login Failed: {error}", gr.update(visible=True), gr.update(visible=False), None # Return None for email display
    else:
        global_user_id = uid
        global_user_email = user_email
        print(f"User {user_email} (UID: {uid}) logged in successfully.")
        # After successful login, hide login tab and show sender tab
        return "Login Successful! Redirecting...", gr.update(visible=False), gr.update(visible=True), f"Logged in as: **{global_user_email}**" # Update email display

def logout_ui_logic():
    global global_user_id, global_user_email, email_logs, global_initial_df
    global_user_id = None
    global_user_email = None
    email_logs = []
    global_initial_df = None
    print("User logged out.")
    # After logout, show login tab and hide sender tab, reset all fields
    return "Logged out successfully.", gr.update(visible=True), gr.update(visible=False), "", None, "", "", None, f"Logged in as: **Guest**" # Reset email display

# --- Email Sending UI and Logic ---
def start_sending_ui_logic(sender_email_input, excel_file_input, subject_template_input, body_template_input, progress=gr.Progress()):
    global current_send_job, email_logs, global_user_id, global_initial_df

    if not global_user_id:
        return "Error: Not logged in. Please log in first.", "", None

    if not GMAIL_APP_PASSWORD:
        return "Error: GMAIL_APP_PASSWORD not set in environment variables. Please check your deployment secrets or .env file.", "", None

    if not excel_file_input:
        return "Error: Please upload an Excel file.", "", None

    email_logs = [] # Reset logs for a new sending operation
    current_send_job["running"] = True
    current_send_job["interrupt"] = False

    # Process Excel file
    initial_df, recipients, excel_error = excel_manager.process_excel_for_sending(excel_file_input)
    if excel_error:
        current_send_job["running"] = False
        return f"Error: {excel_error}", "", None
    if not recipients:
        current_send_job["running"] = False
        return "No recipients found in the Excel file.", "", None

    global_initial_df = initial_df # Store for final Excel generation

    total_recipients = len(recipients)
    progress(0, desc="Starting email send...")

    for i, recipient in enumerate(recipients):
        if current_send_job["interrupt"]:
            message = "Email sending interrupted by user."
            print(message)
            break # Exit the loop if stop is requested

        name = recipient['name']
        email = recipient['email']

        # Personalize subject and body
        personalized_subject = subject_template_input.replace("{Name}", name)
        personalized_body = body_template_input.replace("{Name}", name)

        status_msg = f"Sending to {name} ({email})..."
        print(status_msg)
        progress((i + 1) / total_recipients, desc=status_msg)

        # Send email
        success, send_error = email_manager.send_email_via_smtp(
            sender_email_input, GMAIL_APP_PASSWORD, email, personalized_subject, personalized_body
        )

        log_status = "sent" if success else "failed"
        log_error_msg = send_error if not success else None

        # Create log entry for current send
        log_entry = {
            'userId': global_user_id,
            'email': email,
            'name': name,
            'subject': personalized_subject,
            'body_preview': personalized_body[:100] + '...' if len(personalized_body) > 100 else personalized_body,
            'timestamp': datetime.now(),
            'status': log_status,
            'error': log_error_msg
        }
        email_logs.append(log_entry) # Add to session logs

        # Log to Firebase Firestore
        try:
            db.collection('emailLogs').add(log_entry)
            print(f"Logged to Firestore for {email}: {log_status}")
        except Exception as e:
            print(f"Error logging to Firestore for {email}: {e}")

        # Add delay for responsible sending
        time.sleep(20)

    current_send_job["running"] = False # Mark job as finished/interrupted

    # Generate final Excel for download
    final_excel_buffer, excel_gen_error = excel_manager.generate_final_excel(global_initial_df, email_logs)
    if excel_gen_error:
        final_excel_output = None
        final_excel_message = f"Error generating final Excel: {excel_gen_error}"
    else:
        final_excel_output = final_excel_buffer.getvalue() # Get bytes for download
        final_excel_message = "Email sending complete (or interrupted)!"

    # Prepare current logs for display in Gradio
    current_logs_display_df = pd.DataFrame(email_logs)
    current_logs_display_md = current_logs_display_df.to_markdown(index=False) if not current_logs_display_df.empty else "No logs yet."

    return final_excel_message, current_logs_display_md, gr.File(value=(final_excel_output, "email_results.xlsx"), interactive=True, type="bytes")

def stop_sending_ui_logic():
    """Interrupts the current sending job."""
    if current_send_job["running"]:
        current_send_job["interrupt"] = True
        return "Attempting to stop. Please wait for the current email to finish sending.", gr.update(interactive=False)
    return "No active sending job to stop.", gr.update(interactive=False)

# --- Gradio Interface Definition ---
with gr.Blocks() as demo:
    gr.Markdown("# 📧 Cloud-Based Email Automation Tool")

    # Store a reference to the sender tab, so we can control its visibility programmatically
    sender_tab_block = None 

    with gr.Tab("Login / Authentication") as login_tab_block:
        login_status_output = gr.Markdown("Please log in to use the tool.")
        with gr.Row():
            email_input = gr.Textbox(label="Your Email", placeholder="your@example.com")
            password_input = gr.Textbox(label="Your Password", type="password", placeholder="********")
            login_btn = gr.Button("Login", variant="primary")
        gr.Markdown("*(Note: For this demo, users must be created manually in Firebase Console > Authentication > Users.)*")

    with gr.Tab("Email Sender Dashboard", visible=False) as sender_tab_block_init: # Initially hidden
        sender_tab_block = sender_tab_block_init # Assign to global variable for later use in _js
        gr.Markdown("## Send Personalized Emails")

        user_display_markdown = gr.Markdown(f"### Logged in as: **Guest**") # Will be updated dynamically

        gr.Markdown("---")

        with gr.Row():
            sender_email_input = gr.Textbox(label="Your Gmail Address (Sender)", placeholder="your.gmail@gmail.com", interactive=True)
            excel_upload_input = gr.File(label="Upload Recipients Excel (.xlsx) [Cols: Name, Email]", type="bytes", file_count="single", interactive=True)

        subject_input = gr.Textbox(label="Email Subject (Use {Name} for personalization)", placeholder="Hello {Name}, a special offer for you!")
        body_input = gr.Textbox(label="Email Body (Use {Name} for personalization)", lines=10, placeholder="Hi {Name},\n\nWe wanted to share some exciting news with you...\n\nBest regards,\nYour Team")

        with gr.Row():
            start_send_btn = gr.Button("Start Sending Emails", variant="primary")
            stop_send_btn = gr.Button("STOP Sending", variant="secondary", interactive=False)
            logout_btn = gr.Button("Logout", variant="secondary")

        sending_status_output = gr.Markdown("Status: Ready to send.")
        live_logs_output = gr.Markdown("Live Sending Logs will appear here.")
        download_results_output = gr.File(label="Download Final Results Excel (.xlsx)", file_count="single", interactive=False)

    # --- Button Clicks and UI Updates ---
    login_btn.click(
        login_ui_logic,
        inputs=[email_input, password_input],
        outputs=[login_status_output, login_tab_block, sender_tab_block_init, user_display_markdown], # Pass user_display_markdown to be updated
        _js="""
        (status, login_tab_comp, sender_tab_comp, user_markdown_comp) => {
            if (status.includes("Successful")) {
                const loginTabButton = document.querySelector('button[data-tab-id="0"]'); // Assuming login is the first tab
                const senderTabButton = document.querySelector('button[data-tab-id="1"]'); // Assuming sender is the second tab
                if (loginTabButton) loginTabButton.style.display = 'none'; // Hide login tab button
                if (senderTabButton) senderTabButton.click(); // Programmatically click on sender tab to switch
            }
            return [status, login_tab_comp, sender_tab_comp, user_markdown_comp]; // Return updated components
        }
        """
    )

    start_send_btn.click(
        lambda: gr.update(interactive=True), # Enable stop button immediately
        outputs=[stop_send_btn],
        queue=False # This UI update should happen instantly
    ).then(
        start_sending_ui_logic,
        inputs=[sender_email_input, excel_upload_input, subject_input, body_input],
        outputs=[sending_status_output, live_logs_output, download_results_output],
    ).then(
        lambda: gr.update(interactive=False), # Disable stop button after sending is done
        outputs=[stop_send_btn],
        queue=False
    )

    stop_send_btn.click(
        stop_sending_ui_logic,
        outputs=[sending_status_output, stop_send_btn],
        queue=False # This UI update should happen instantly
    )

    logout_btn.click(
        logout_ui_logic,
        outputs=[
            login_status_output,       # Login status message
            login_tab_block,           # Login tab visibility
            sender_tab_block_init,     # Sender tab visibility
            sender_email_input,        # Clear sender email input
            excel_upload_input,        # Clear excel upload
            subject_input,             # Clear subject
            body_input,                # Clear body
            download_results_output,   # Clear download output
            user_display_markdown      # Update user display markdown
        ],
        _js="""
        (status, login_tab_comp, sender_tab_comp, sender_email_val, excel_upload_val, subject_val, body_val, download_output_val, user_markdown_comp) => {
            const loginTabButton = document.querySelector('button[data-tab-id="0"]');
            const senderTabButton = document.querySelector('button[data-tab-id="1"]');
            if (loginTabButton) loginTabButton.style.display = 'block'; // Show login tab button
            if (loginTabButton) loginTabButton.click(); // Switch to login tab

            // Clear inputs and outputs
            // Note: For File and Textbox components, assigning null or empty string might not visually clear them immediately
            // without a full Gradio refresh or specific JS to manipulate the internal component state.
            // However, the backend state will be reset.
            return [status, login_tab_comp, sender_tab_comp, "", null, "", "", null, user_markdown_comp]; // Return null for inputs to clear them (backend state)
        }
        """
    )


# Launch the Gradio app
if __name__ == "__main__":
    demo.launch(debug=True, share=False) # Set share=True for a public temporary link for testing
