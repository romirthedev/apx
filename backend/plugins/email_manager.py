"""
Email Manager Plugin - Handle email operations and calendar management
"""

import os
import subprocess
import logging
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class EmailManager:
    def __init__(self):
        self.supported_clients = ['mail', 'outlook', 'gmail', 'thunderbird']
        self.calendar_apps = ['calendar', 'outlook', 'google calendar']
    
    def compose_email(self, to: str = "", subject: str = "", body: str = "", cc: str = "", bcc: str = "") -> str:
        """Compose a new email using the default mail client."""
        try:
            # Build mailto URL
            params = {}
            if subject:
                params['subject'] = subject
            if body:
                params['body'] = body
            if cc:
                params['cc'] = cc
            if bcc:
                params['bcc'] = bcc
            
            # Create mailto URL
            mailto_url = f"mailto:{to}"
            if params:
                query_string = urllib.parse.urlencode(params)
                mailto_url += f"?{query_string}"
            
            # Open default mail client
            subprocess.run(['open', mailto_url], check=True)
            
            recipient_info = f" to {to}" if to else ""
            return f"✅ Opened email composition{recipient_info} in default mail client"
            
        except Exception as e:
            logger.error(f"Failed to compose email: {str(e)}")
            return f"❌ Failed to open email client: {str(e)}"
    
    def send_quick_email(self, to: str, subject: str, message: str) -> str:
        """Send a quick email using AppleScript (macOS Mail app)."""
        try:
            applescript = f'''
            tell application "Mail"
                set newMessage to make new outgoing message with properties {{subject:"{subject}", content:"{message}"}}
                tell newMessage
                    make new to recipient with properties {{address:"{to}"}}
                    send
                end tell
            end tell
            '''
            
            # Execute AppleScript
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, check=True)
            
            return f"✅ Quick email sent to {to} with subject: {subject}"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"AppleScript failed: {e.stderr}")
            # Retry with direct Mail.app activation
            try:
                subprocess.run([
                    'osascript', '-e', 
                    f'tell application "Mail" to activate'
                ], check=True)
                return self.compose_email(to, subject, message)
            except Exception as retry_e:
                logger.error(f"Fallback failed: {str(retry_e)}")
                return f"❌ Failed to send email: {str(e)}. Please check Mail.app settings."
        except Exception as e:
            logger.error(f"Failed to send quick email: {str(e)}")
            return f"❌ Failed to send email: {str(e)}"
    
    def create_meeting_invite(self, title: str, attendees: List[str], 
                            start_time: str, duration: int = 60, 
                            location: str = "", notes: str = "") -> str:
        """Create a calendar meeting invite."""
        try:
            # Parse start time - assume format like "2024-01-15 14:00" or "tomorrow 2pm"
            if "tomorrow" in start_time.lower():
                base_date = datetime.now() + timedelta(days=1)
                if "pm" in start_time.lower():
                    hour = int(start_time.split()[1].replace("pm", ""))
                    if hour != 12:
                        hour += 12
                else:
                    hour = int(start_time.split()[1].replace("am", ""))
                start_dt = base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            else:
                # Try to parse as datetime
                try:
                    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
                except ValueError:
                    start_dt = datetime.now() + timedelta(hours=1)  # Default to 1 hour from now
            
            end_dt = start_dt + timedelta(minutes=duration)
            
            # Format for calendar
            start_formatted = start_dt.strftime("%Y%m%dT%H%M%S")
            end_formatted = end_dt.strftime("%Y%m%dT%H%M%S")
            
            # Create AppleScript for Calendar.app
            attendees_str = ", ".join(attendees)
            applescript = f'''
            tell application "Calendar"
                tell calendar "Calendar"
                    set newEvent to make new event with properties {{
                        summary:"{title}",
                        start date:(date "{start_dt.strftime('%m/%d/%Y %H:%M:%S')}"),
                        end date:(date "{end_dt.strftime('%m/%d/%Y %H:%M:%S')}"),
                        location:"{location}",
                        description:"{notes}\\n\\nAttendees: {attendees_str}"
                    }}
                end tell
                show newEvent
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, check=True)
            
            return f"✅ Created meeting '{title}' for {start_dt.strftime('%Y-%m-%d %H:%M')} with {len(attendees)} attendees"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Calendar AppleScript failed: {e.stderr}")
            # Fallback: create ICS file
            return self._create_ics_file(title, attendees, start_time, duration, location, notes)
        except Exception as e:
            logger.error(f"Failed to create meeting: {str(e)}")
            return f"❌ Failed to create meeting: {str(e)}"
    
    def _create_ics_file(self, title: str, attendees: List[str], 
                        start_time: str, duration: int, 
                        location: str, notes: str) -> str:
        """Create an ICS calendar file as fallback."""
        try:
            # Parse start time
            if "tomorrow" in start_time.lower():
                base_date = datetime.now() + timedelta(days=1)
                if "pm" in start_time.lower():
                    hour = int(start_time.split()[1].replace("pm", ""))
                    if hour != 12:
                        hour += 12
                else:
                    hour = int(start_time.split()[1].replace("am", ""))
                start_dt = base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            else:
                try:
                    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
                except ValueError:
                    start_dt = datetime.now() + timedelta(hours=1)
            
            end_dt = start_dt + timedelta(minutes=duration)
            
            # Format for ICS
            start_formatted = start_dt.strftime("%Y%m%dT%H%M%S")
            end_formatted = end_dt.strftime("%Y%m%dT%H%M%S")
            
            # Create ICS content
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:Cluely
BEGIN:VEVENT
UID:{start_formatted}@cluely.local
DTSTART:{start_formatted}
DTEND:{end_formatted}
SUMMARY:{title}
LOCATION:{location}
DESCRIPTION:{notes}\\n\\nAttendees: {', '.join(attendees)}
END:VEVENT
END:VCALENDAR"""
            
            # Save to file
            filename = f"meeting_{start_dt.strftime('%Y%m%d_%H%M')}.ics"
            filepath = os.path.expanduser(f"~/Desktop/{filename}")
            
            with open(filepath, 'w') as f:
                f.write(ics_content)
            
            # Open the file
            subprocess.run(['open', filepath], check=True)
            
            return f"✅ Created calendar file: {filename} (saved to Desktop)"
            
        except Exception as e:
            logger.error(f"Failed to create ICS file: {str(e)}")
            return f"❌ Failed to create calendar file: {str(e)}"
    
    def check_calendar(self, date: str = "today") -> str:
        """Check calendar for a specific date."""
        try:
            # Determine target date
            if date.lower() == "today":
                target_date = datetime.now()
            elif date.lower() == "tomorrow":
                target_date = datetime.now() + timedelta(days=1)
            else:
                try:
                    target_date = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    return "❌ Invalid date format. Use 'today', 'tomorrow', or 'YYYY-MM-DD'"
            
            date_str = target_date.strftime("%m/%d/%Y")
            
            # Use AppleScript to get calendar events
            applescript = f'''
            tell application "Calendar"
                set eventList to ""
                repeat with cal in calendars
                    set calEvents to events of cal whose start date ≥ (date "{date_str}") and start date < (date "{date_str}") + 1 * days
                    repeat with evt in calEvents
                        set eventList to eventList & (summary of evt) & " at " & (start date of evt) & "\\n"
                    end repeat
                end repeat
                return eventList
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, check=True)
            
            events = result.stdout.strip()
            if events:
                return f"📅 Calendar for {target_date.strftime('%Y-%m-%d')}:\\n{events}"
            else:
                return f"📅 No events found for {target_date.strftime('%Y-%m-%d')}"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Calendar check failed: {e.stderr}")
            return f"❌ Failed to check calendar: {e.stderr}"
        except Exception as e:
            logger.error(f"Failed to check calendar: {str(e)}")
            return f"❌ Failed to check calendar: {str(e)}"
    
    def switch_google_account(self, account_email: str = "") -> str:
        """Switch Google account in Chrome."""
        try:
            if not account_email:
                # Open Google account switcher
                url = "https://accounts.google.com/AccountChooser"
            else:
                # Try to switch to specific account
                url = f"https://accounts.google.com/AccountChooser?Email={account_email}"
            
            # Open in Chrome
            subprocess.run(['open', '-a', 'Google Chrome', url], check=True)
            
            if account_email:
                return f"✅ Opened Google account switcher for {account_email}"
            else:
                return "✅ Opened Google account switcher"
            
        except Exception as e:
            logger.error(f"Failed to switch Google account: {str(e)}")
            return f"❌ Failed to switch Google account: {str(e)}"
    
    def open_gmail(self, account: str = "") -> str:
        """Open Gmail in the browser."""
        try:
            if account:
                # Try to open specific Gmail account
                url = f"https://mail.google.com/mail/u/{account}"
            else:
                url = "https://mail.google.com"
            
            subprocess.run(['open', url], check=True)
            
            if account:
                return f"✅ Opened Gmail for account: {account}"
            else:
                return "✅ Opened Gmail"
            
        except Exception as e:
            logger.error(f"Failed to open Gmail: {str(e)}")
            return f"❌ Failed to open Gmail: {str(e)}"
    
    def open_google_calendar(self, account: str = "") -> str:
        """Open Google Calendar in the browser."""
        try:
            if account:
                url = f"https://calendar.google.com/calendar/u/{account}"
            else:
                url = "https://calendar.google.com"
            
            subprocess.run(['open', url], check=True)
            
            if account:
                return f"✅ Opened Google Calendar for account: {account}"
            else:
                return "✅ Opened Google Calendar"
            
        except Exception as e:
            logger.error(f"Failed to open Google Calendar: {str(e)}")
            return f"❌ Failed to open Google Calendar: {str(e)}"
    
    def create_email_template(self, template_name: str, subject: str, body: str) -> str:
        """Create and save an email template."""
        try:
            templates_dir = os.path.expanduser("~/Documents/Email_Templates")
            os.makedirs(templates_dir, exist_ok=True)
            
            template_data = {
                'subject': subject,
                'body': body,
                'created': datetime.now().isoformat()
            }
            
            import json
            template_file = os.path.join(templates_dir, f"{template_name}.json")
            
            with open(template_file, 'w') as f:
                json.dump(template_data, f, indent=2)
            
            return f"✅ Email template '{template_name}' saved to ~/Documents/Email_Templates/"
            
        except Exception as e:
            logger.error(f"Failed to create email template: {str(e)}")
            return f"❌ Failed to create email template: {str(e)}"
    
    def use_email_template(self, template_name: str, to: str = "", **replacements) -> str:
        """Use a saved email template."""
        try:
            templates_dir = os.path.expanduser("~/Documents/Email_Templates")
            template_file = os.path.join(templates_dir, f"{template_name}.json")
            
            if not os.path.exists(template_file):
                return f"❌ Email template '{template_name}' not found"
            
            import json
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            subject = template_data['subject']
            body = template_data['body']
            
            # Replace placeholders
            for key, value in replacements.items():
                placeholder = f"{{{key}}}"
                subject = subject.replace(placeholder, str(value))
                body = body.replace(placeholder, str(value))
            
            return self.compose_email(to, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to use email template: {str(e)}")
            return f"❌ Failed to use email template: {str(e)}"
    
    def get_email_templates(self) -> str:
        """List available email templates."""
        try:
            templates_dir = os.path.expanduser("~/Documents/Email_Templates")
            
            if not os.path.exists(templates_dir):
                return "📧 No email templates found. Create some with 'create email template'!"
            
            templates = []
            for file in os.listdir(templates_dir):
                if file.endswith('.json'):
                    template_name = file.replace('.json', '')
                    templates.append(template_name)
            
            if templates:
                return f"📧 Available email templates:\\n• " + "\\n• ".join(templates)
            else:
                return "📧 No email templates found in ~/Documents/Email_Templates/"
            
        except Exception as e:
            logger.error(f"Failed to list email templates: {str(e)}")
            return f"❌ Failed to list email templates: {str(e)}"
    
    def ai_compose_email(self, recipient: str, idea: str, ai_client=None) -> str:
        """Use AI to compose an email based on a general idea."""
        try:
            if not ai_client:
                return "❌ AI client not available for email composition"
            
            # Create prompt for AI to generate email content
            prompt = f"""Write a professional email to {recipient} about the following: {idea}
            
            Format the response as a JSON with 'subject' and 'body' fields.
            Keep the subject concise and relevant.
            The body should be professional, clear, and well-structured.
            Do not include any salutations or signatures - just the main content.
            """
            
            # Get AI response
            ai_response = ai_client.generate_text(prompt)
            
            try:
                # Parse JSON response
                import json
                email_content = json.loads(ai_response)
                subject = email_content.get('subject', f"About: {idea}")
                body = email_content.get('body', ai_response)
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                subject = f"About: {idea}"
                body = ai_response
            
            # Send the email
            return self.send_quick_email(recipient, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to AI compose email: {str(e)}")
            return f"❌ Failed to AI compose email: {str(e)}"
    
    def summarize_inbox(self, count: int = 5, ai_client=None) -> str:
        """Summarize recent emails from the inbox using AI."""
        try:
            if not ai_client:
                return "❌ AI client not available for email summarization"
            
            # Use AppleScript to get recent emails from Mail.app
            applescript = f'''
            tell application "Mail"
                set emailCount to {count}
                set emailData to {{}}
                set selectedMailbox to inbox
                set theMessages to (messages of selectedMailbox)
                
                repeat with i from 1 to emailCount
                    if i > (count of theMessages) then
                        exit repeat
                    end if
                    
                    set theMessage to item i of theMessages
                    set theSubject to subject of theMessage
                    set theSender to sender of theMessage
                    set theDate to date received of theMessage
                    set theContent to content of theMessage
                    
                    set end of emailData to "FROM: " & theSender & "|SUBJECT: " & theSubject & "|DATE: " & theDate & "|CONTENT: " & theContent
                end repeat
                
                return emailData
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, check=True)
            
            emails_raw = result.stdout.strip()
            
            if not emails_raw:
                return "📥 No recent emails found in inbox"
            
            # Format emails for AI processing
            emails = emails_raw.split(", ")
            emails_formatted = "\n\n".join([email.strip('"') for email in emails])
            
            # Create prompt for AI to summarize emails
            prompt = f"""Summarize the following {count} emails from my inbox:
            
            {emails_formatted}
            
            Provide a concise summary of each email and highlight any that require urgent attention.
            Format the response in a clear, readable way with bullet points for each email.
            """
            
            # Get AI summary
            summary = ai_client.generate_text(prompt)
            
            return f"📥 Email Inbox Summary:\n\n{summary}"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Mail.app AppleScript failed: {e.stderr}")
            return self._fallback_email_summary(count, ai_client)
        except Exception as e:
            logger.error(f"Failed to summarize inbox: {str(e)}")
            return f"❌ Failed to summarize inbox: {str(e)}"
    
    def _fallback_email_summary(self, count: int, ai_client) -> str:
        """Fallback method to summarize emails using Gmail in browser."""
        try:
            # Open Gmail
            self.open_gmail()
            
            return f"📥 Opened Gmail in browser. Please use the AI to summarize visible emails."
            
        except Exception as e:
            logger.error(f"Failed to use fallback email summary: {str(e)}")
            return f"❌ Failed to summarize emails: {str(e)}"
