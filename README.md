# 📧 Cloud-Based Email Automation Tool

A Python-based email automation tool with a Gradio UI, integrated with Firebase for authentication and logging. Designed for seamless deployment via GitHub to a cloud hosting service (like Firebase Hosting with Cloud Functions, to be covered in next steps).

## ✨ Features

* **Secure User Login:** Each user authenticates with their own Firebase-managed email/password.
* **Excel File Upload:** Easily upload `.xlsx` files containing `Name` and `Email` columns for recipients.
* **Personalized Emails:** Craft dynamic subject lines and email bodies with `{Name}` placeholder for personalized messages.
* **Gmail SMTP Integration:** Send emails securely using your Gmail account (requires an App Password for 2-Step Verification enabled accounts).
* **Live Sending Logs:** Monitor the status (✅ Sent / ❌ Failed) of each email in real-time within the UI.
* **Stop Functionality:** Interrupt an ongoing email sending process at any time.
* **Downloadable Results:** Get a final Excel file with send statuses and any error details.
* **Firebase Firestore Logging:** All email sending activities are logged to your Firebase Firestore database for persistent records.
* **Modular Codebase:** Organized into separate Python modules (`auth_handler.py`, `email_sender.py`, `excel_handler.py`, `firebase_handler.py`) for maintainability and scalability.

## 🚀 Getting Started (Local Development)

### 1. Clone the Repository

Sabse pehle, apne computer par is code ko download karein:

```bash
git clone [https://github.com/khalil397/email-automation-tool.git](https://github.com/khalil397/email-automation-tool.git)
cd email-automation-tool
