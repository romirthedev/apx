
import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    _GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    _GOOGLE_CALENDAR_AVAILABLE = False

class CalendarIntegrationError(Exception):
    """Custom exception for calendar integration errors."""
    pass

class CalendarScheduler:
    """
    A class to interact with calendar services for scheduling events.

    This class provides functionality to create and schedule events directly
    on a user's calendar, integrating with services like Google Calendar.
    """

    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        """
        Initializes the CalendarScheduler.

        Args:
            credentials_path: Path to the OAuth 2.0 client secrets file.
            token_path: Path to store the user's access and refresh tokens.
        """
        if not _GOOGLE_CALENDAR_AVAILABLE:
            raise CalendarIntegrationError(
                "Google Calendar API client library is not installed. "
                "Please install it using: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._service = self._get_calendar_service()

    def _get_calendar_service(self) -> Any:
        """
        Authenticates with the Google Calendar API and returns the service object.

        This method handles the OAuth 2.0 flow for obtaining user credentials.
        It will attempt to load existing tokens and, if they are invalid or
        missing, will guide the user through the authentication process.

        Returns:
            A Google Calendar API service object.

        Raises:
            CalendarIntegrationError: If authentication fails or required libraries are missing.
        """
        creds = None
        try:
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first time.
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, self._get_scopes())

            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Use a tool like google-auth-oauthlib to handle the flow.
                    # For a production system, you'd likely want a more robust
                    # way to handle the authorization flow, perhaps via a web UI.
                    # This example assumes a local development environment where
                    # a browser can be opened.
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self._get_scopes())
                    creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())

            service = build('calendar', 'v3', credentials=creds)
            return service

        except FileNotFoundError:
            raise CalendarIntegrationError(
                f"Credentials file not found at '{self.credentials_path}'. "
                "Please ensure the file exists and contains your Google API client secrets."
            )
        except Exception as e:
            raise CalendarIntegrationError(f"Failed to authenticate with Google Calendar API: {e}")

    def _get_scopes(self) -> List[str]:
        """
        Returns the required OAuth 2.0 scopes for calendar access.
        """
        return ['https://www.googleapis.com/auth/calendar.events']

    def schedule_meeting(
        self,
        attendee_email: str,
        summary: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schedules a meeting event on the user's calendar.

        Args:
            attendee_email: The email address of the primary attendee.
                            This will be set as the organizer if no other organizer is specified.
            summary: The title or summary of the meeting.
            start_time: The start datetime of the meeting.
            end_time: The end datetime of the meeting.
            description: Optional description for the event.
            location: Optional location for the event.

        Returns:
            A dictionary containing the details of the created calendar event.

        Raises:
            CalendarIntegrationError: If the event cannot be scheduled due to API errors
                                      or invalid input.
        """
        if not self._service:
            raise CalendarIntegrationError("Calendar service is not initialized. Authentication failed.")

        if start_time >= end_time:
            raise CalendarIntegrationError("Start time must be before end time.")

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': str(start_time.tzinfo) if start_time.tzinfo else 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': str(end_time.tzinfo) if end_time.tzinfo else 'UTC',
            },
            'attendees': [
                {'email': attendee_email},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        try:
            created_event = self._service.events().insert(calendarId='primary', body=event).execute()
            return {
                'id': created_event.get('id'),
                'summary': created_event.get('summary'),
                'htmlLink': created_event.get('htmlLink'),
                'start': created_event['start'],
                'end': created_event['end'],
                'attendees': created_event.get('attendees', []),
                'status': created_event.get('status'),
            }
        except HttpError as error:
            raise CalendarIntegrationError(f"An API error occurred while scheduling the meeting: {error}")
        except Exception as e:
            raise CalendarIntegrationError(f"An unexpected error occurred while scheduling the meeting: {e}")

# Example of how to use the class (for demonstration purposes, not part of the module itself)
if __name__ == '__main__':
    import os

    # Ensure you have a 'credentials.json' file in the same directory or provide the full path.
    # This file is obtained from the Google Cloud Console when setting up a project and
    # enabling the Google Calendar API.

    # IMPORTANT: For this example to run, you need to have:
    # 1. A Google Cloud Project set up.
    # 2. Enabled the Google Calendar API for your project.
    # 3. Created an OAuth 2.0 Client ID (Desktop app type).
    # 4. Downloaded the 'credentials.json' file and placed it in the same directory
    #    as this script, or updated the `credentials_path`.
    # 5. Installed the necessary libraries:
    #    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

    # Replace with the actual email you want to schedule the meeting with.
    # For testing, it's often useful to schedule with your own email address first.
    TEST_ATTENDEE_EMAIL = "clanrxvenge@gmail.com" # Placeholder from user request

    # Define event details
    meeting_summary = "Project Sync Meeting"
    now = datetime.datetime.now(datetime.timezone.utc)
    start_datetime = now + datetime.timedelta(hours=1)
    end_datetime = start_datetime + datetime.timedelta(minutes=30)
    meeting_description = "Weekly sync to discuss project progress and upcoming tasks."
    meeting_location = "Virtual Meeting Room"

    try:
        # Create an instance of the CalendarScheduler
        # The token.json file will be created automatically upon first authentication.
        scheduler = CalendarScheduler(
            credentials_path="credentials.json",
            token_path="token.json"
        )

        print(f"Attempting to schedule a meeting with {TEST_ATTENDEE_EMAIL}...")
        scheduled_event_details = scheduler.schedule_meeting(
            attendee_email=TEST_ATTENDEE_EMAIL,
            summary=meeting_summary,
            start_time=start_datetime,
            end_time=end_datetime,
            description=meeting_description,
            location=meeting_location,
        )

        print("\nMeeting successfully scheduled!")
        print(f"Event ID: {scheduled_event_details['id']}")
        print(f"Summary: {scheduled_event_details['summary']}")
        print(f"Start Time: {scheduled_event_details['start']['dateTime']}")
        print(f"End Time: {scheduled_event_details['end']['dateTime']}")
        print(f"Link: {scheduled_event_details['htmlLink']}")

    except CalendarIntegrationError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print("Error: 'credentials.json' not found. Please ensure you have downloaded "
              "your Google API client secrets and placed it in the correct location.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
