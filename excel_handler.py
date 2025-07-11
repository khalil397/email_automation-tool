# excel_handler.py
import pandas as pd
import io

class ExcelHandler:
    def process_excel_for_sending(self, excel_file_bytes):
        """
        Reads an Excel file from bytes, expects 'Name' and 'Email' columns.
        Returns a pandas DataFrame and a list of dictionaries with 'name' and 'email'.
        """
        try:
            # Read Excel file from BytesIO object provided by Gradio
            df = pd.read_excel(io.BytesIO(excel_file_bytes))
            required_columns = ['Name', 'Email']
            if not all(col in df.columns for col in required_columns):
                raise ValueError("Excel file must contain 'Name' and 'Email' columns.")

            recipients = []
            for index, row in df.iterrows():
                recipients.append({
                    'name': str(row['Name']).strip(),
                    'email': str(row['Email']).strip()
                })
            return df, recipients, None # Return original DataFrame, recipients list, and no error
        except Exception as e:
            return None, None, f"Error processing Excel file: {e}"

    def generate_final_excel(self, initial_df, log_data):
        """
        Generates a new Excel file with send statuses merged with the initial DataFrame.
        `initial_df` is the pandas DataFrame loaded from the user's initial upload.
        `log_data` is a list of dictionaries with log entries.
        """
        try:
            if not log_data:
                # If no logs, just return the original DataFrame with empty status columns
                initial_df['Status'] = 'Not Processed'
                initial_df['Error Details'] = ''
                initial_df['Sent Timestamp'] = ''
                final_df = initial_df[['Name', 'Email', 'Status', 'Error Details', 'Sent Timestamp']]
            else:
                log_df = pd.DataFrame(log_data)

                # Ensure 'email' column is string type for merging
                initial_df['Email'] = initial_df['Email'].astype(str)
                log_df['email'] = log_df['email'].astype(str)

                # Merge the original DataFrame with the log data based on email
                merged_df = pd.merge(initial_df, log_df[['email', 'status', 'error', 'timestamp']],
                                     left_on='Email', right_on='email', how='left')

                # Clean up merged columns and rename for clarity
                merged_df['Status'] = merged_df['status'].fillna('Not Sent').apply(lambda x: '✅ Sent' if x == 'sent' else ('❌ Failed' if x == 'failed' else x))
                merged_df['Error Details'] = merged_df['error'].fillna('')
                merged_df['Sent Timestamp'] = merged_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')

                final_df = merged_df[['Name', 'Email', 'Status', 'Error Details', 'Sent Timestamp']]

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Email Results')
            output.seek(0)
            return output, None
        except Exception as e:
            return None, f"Error generating final Excel: {e}"

# Instantiate the ExcelHandler
excel_manager = ExcelHandler()
