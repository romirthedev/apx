
import datetime
import logging
import re
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CalendarEventManager:
    """
    A specialized tool class to manage calendar events, focusing on creating events.
    This class is designed to simulate event creation with granular control
    for date, time, and title, addressing the user's specific request.
    """

    def __init__(self) -> None:
        """Initializes the CalendarEventManager."""
        logging.info("CalendarEventManager initialized.")

    def _parse_time_string(self, time_str: str) -> datetime.time:
        """
        Parses a time string, supporting HH:MM and H AM/PM formats.

        Args:
            time_str: The time string to parse.

        Returns:
            A datetime.time object.

        Raises:
            ValueError: If the time string is invalid or not in a supported format.
        """
        # Try HH:MM format first
        try:
            time_components = time_str.split(":")
            if len(time_components) == 2:
                hours = int(time_components[0])
                minutes = int(time_components[1])
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    raise ValueError("Hour or minute value out of range.")
                return datetime.time(hours, minutes)
        except ValueError:
            pass # Try next format

        # Try H AM/PM format
        time_regex_h_am_pm = r'^(\d{1,2})\s*(am|pm)$'
        match_h_am_pm = re.match(time_regex_h_am_pm, time_str, re.IGNORECASE)
        if match_h_am_pm:
            try:
                time_val = match_h_am_pm.group(0) # Full matched string like "2 pm"
                time_obj = datetime.datetime.strptime(time_val, '%I %p')
                return time_obj.time()
            except ValueError:
                pass # Should not happen if regex matches, but good practice

        raise ValueError("Invalid time format. Expected HH:MM or H AM/PM (e.g., '14:00' or '2 PM').")

    def create_event_for_tomorrow(self, title: str, time_str: str) -> Dict[str, Any]:
        """
        Creates a simulated calendar event for tomorrow at a specified time.

        This method calculates tomorrow's date and parses the provided time string.
        It then returns a structured dictionary representing the planned event.
        This implementation does not modify any actual calendar system.

        Args:
            title: The title of the event.
            time_str: The time of the event in a format recognizable by _parse_time_string.

        Returns:
            A dictionary containing:
                'success' (bool): True if the operation was successful, False otherwise.
                'message' (str): A human-readable message describing the outcome.
                'event_details' (Optional[Dict[str, Any]]): Details of the planned event if successful.
        """
        if not title or not time_str:
            logging.error("Event title and time string are required for event creation.")
            return {
                "success": False,
                "message": "Event title and time string are required.",
                "event_details": None
            }

        try:
            # Calculate tomorrow's date
            today = datetime.date.today()
            tomorrow = today + datetime.timedelta(days=1)

            # Parse the time string using the dedicated helper
            event_time = self._parse_time_string(time_str)

            event_datetime = datetime.datetime.combine(tomorrow, event_time)

            event_details = {
                "title": title,
                "start_datetime": event_datetime.isoformat(),
                "end_datetime": (event_datetime + datetime.timedelta(minutes=30)).isoformat(), # Assume 30 min duration
                "description": f"Simulated calendar event: {title}",
                "location": None,
                "calendar": "default" # Placeholder for calendar name
            }

            logging.info(f"Successfully planned simulated event: '{title}' for {event_datetime.strftime('%Y-%m-%d %H:%M')}")
            return {
                "success": True,
                "message": f"Calendar event '{title}' planned for tomorrow at {event_datetime.strftime('%I:%M %p').lower()}.",
                "event_details": event_details
            }

        except ValueError as ve:
            logging.error(f"Error parsing time or creating event: {ve}")
            return {
                "success": False,
                "message": f"Invalid input: {ve}",
                "event_details": None
            }
        except Exception as e:
            logging.error(f"An unexpected error occurred during event creation: {e}")
            return {
                "success": False,
                "message": f"An unexpected error occurred: {e}",
                "event_details": None
            }

    def handle_user_request(self, request: str) -> Dict[str, Any]:
        """
        Parses a user request string and creates a calendar event if applicable.

        This method attempts to understand requests like "Create a calendar event for tomorrow at 2 PM titled Meeting with John"
        and extracts the necessary components (title, time) to call the core event creation function.

        Args:
            request: The user's natural language request.

        Returns:
            A dictionary containing:
                'success' (bool): True if the operation was successful, False otherwise.
                'message' (str): A human-readable message describing the outcome.
                'event_details' (Optional[Dict[str, Any]]): Details of the planned event if successful.
        """
        logging.info(f"Handling user request: '{request}'")

        # Keywords to identify a calendar event creation request
        create_keywords = ["create", "add", "new", "schedule", "make"]
        calendar_keywords = ["calendar", "event", "meeting", "appointment"]
        tomorrow_keywords = ["tomorrow"]
        at_keywords = ["at"]
        titled_keywords = ["titled", "title", "called"]

        request_lower = request.lower()

        # Basic check if the request is about creating a calendar event
        if not any(kw in request_lower for kw in create_keywords) or \
           not any(kw in request_lower for kw in calendar_keywords):
            logging.warning(f"Request does not appear to be a calendar event creation request: '{request}'")
            return {
                "success": False,
                "message": "I can only help create calendar events. Please ask me to 'create a calendar event'.",
                "event_details": None
            }

        # Ensure 'tomorrow' is specified
        if "tomorrow" not in request_lower:
            logging.warning(f"Request does not specify 'tomorrow': '{request}'")
            return {
                "success": False,
                "message": "Please specify 'tomorrow' as the date for the event.",
                "event_details": None
            }

        try:
            # --- Extracting Time ---
            time_match_str = None
            # Use regex to find time patterns more robustly around 'at'
            # This regex looks for patterns like "at 2 PM", "at 14:00", "at 2:30pm"
            time_pattern = r"(?:at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)"
            time_match = re.search(time_pattern, request, re.IGNORECASE)

            if time_match:
                potential_time = time_match.group(1)
                # Further validate if it's a parsable time
                try:
                    parsed_time = self._parse_time_string(potential_time)
                    time_match_str = potential_time # Store the original string for the message if needed, but use parsed for logic
                except ValueError:
                    logging.warning(f"Found a potential time '{potential_time}' but it's invalid.")
                    pass # Continue to look for title, might have a valid time later or report error

            if not time_match_str: # If the first regex didn't find a parsable time
                 # Fallback for simpler cases or if 'at' is not used explicitly before time
                for kw in at_keywords:
                    if kw in request_lower:
                        parts = request.split(kw, 1)
                        if len(parts) > 1:
                            potential_time_part = parts[1].strip()
                            # Look for HH:MM or H AM/PM pattern more directly
                            # Prioritize HH:MM
                            time_regex_hh_mm = r'^(\d{1,2}:\d{2})'
                            time_regex_h_am_pm = r'^(\d{1,2}\s*(?:am|pm))'

                            match_hh_mm = re.match(time_regex_hh_mm, potential_time_part, re.IGNORECASE)
                            if match_hh_mm:
                                try:
                                    self._parse_time_string(match_hh_mm.group(1)) # Validate
                                    time_match_str = match_hh_mm.group(1)
                                    break
                                except ValueError:
                                    pass

                            if not time_match_str: # If HH:MM didn't work, try H AM/PM
                                match_h_am_pm = re.match(time_regex_h_am_pm, potential_time_part, re.IGNORECASE)
                                if match_h_am_pm:
                                    try:
                                        self._parse_time_string(match_h_am_pm.group(1)) # Validate
                                        time_match_str = match_h_am_pm.group(1)
                                        break
                                    except ValueError:
                                        pass
            if not time_match_str:
                logging.warning(f"Could not extract a valid time from request: '{request}'")
                return {
                    "success": False,
                    "message": "Please specify the time for the event (e.g., 'at 2 PM' or 'at 14:00').",
                    "event_details": None
                }

            # --- Extracting Title ---
            title_match_str = None
            # More robust title extraction: find "titled" or "title" and take the rest,
            # also handle cases where title might be at the beginning or middle.
            for kw in titled_keywords:
                if kw in request_lower:
                    parts = request.split(kw, 1)
                    if len(parts) > 1:
                        potential_title_part = parts[1].strip()
                        # Remove common trailing punctuation and trim
                        title_match_str = re.sub(r'[.,!?;:]+$', '', potential_title_part).strip()
                        if title_match_str:
                            break

            # If 'titled' keyword wasn't found, try to infer title if it's the remaining part after time/date
            if not title_match_str:
                # A simple heuristic: if we found time and date (tomorrow), assume the remaining is the title
                # This is a simplification and might need more advanced NLP for complex sentences.
                # For the specific request "Create a calendar event for tomorrow at 2 PM titled Meeting with John"
                # the 'titled' keyword approach works well. If 'titled' is missing, we could try to
                # extract parts of the sentence that are not recognized as date/time.
                # For now, we'll rely on the 'titled' keyword being present for clearer extraction.
                logging.warning(f"Could not explicitly find a title using keywords like 'titled' in request: '{request}'")
                # Let's refine the approach slightly: try to find the part of the string that is NOT the date/time.
                # This is still heuristic.
                date_part = "tomorrow"
                # Construct a pattern to find the date and time together
                # This is tricky as order can vary. A simpler approach is to rely on the keywords.

                # Let's stick to the "titled" keyword for robust title extraction for now.
                # If it's not there, we'll ask the user to be more specific.
                return {
                    "success": False,
                    "message": "Please specify the title of the event using keywords like 'titled', 'title', or 'called' (e.g., 'titled Meeting with John').",
                    "event_details": None
                }


            # --- Call the core event creation method with extracted parameters ---
            logging.info(f"Extracted Title: '{title_match_str}', Time: '{time_match_str}'")
            return self.create_event_for_tomorrow(title=title_match_str, time_str=time_match_str)

        except ValueError as ve:
            # This catches errors from _parse_time_string specifically if it was called directly in error path
            logging.error(f"ValueError during request parsing: {ve}")
            return {
                "success": False,
                "message": f"Invalid input or format error: {ve}",
                "event_details": None
            }
        except Exception as e:
            logging.error(f"An unexpected error occurred during request parsing: {e}")
            return {
                "success": False,
                "message": f"Could not process your request due to an unexpected error: {e}",
                "event_details": None
            }

# Example of how to use the class (optional, for testing)
if __name__ == "__main__":
    manager = CalendarEventManager()

    print("--- Test Cases ---")

    # User Request: "Create a calendar event for tomorrow at 2 PM titled Meeting with John"
    user_request_1 = "Create a calendar event for tomorrow at 2 PM titled Meeting with John"
    print(f"\nRequest: '{user_request_1}'")
    result_1 = manager.handle_user_request(user_request_1)
    print(f"Result: {result_1}")
    # Expected: Success=True, title="Meeting with John", start_datetime for tomorrow 14:00

    # User Request: "Add a new meeting tomorrow at 9:30 AM titled Project Sync"
    user_request_2 = "Add a new meeting tomorrow at 9:30 AM titled Project Sync"
    print(f"\nRequest: '{user_request_2}'")
    result_2 = manager.handle_user_request(user_request_2)
    print(f"Result: {result_2}")
    # Expected: Success=True, title="Project Sync", start_datetime for tomorrow 09:30

    # User Request: "Schedule an event for tomorrow at 15:00 called 'Client Call'"
    user_request_3 = "Schedule an event for tomorrow at 15:00 called 'Client Call'"
    print(f"\nRequest: '{user_request_3}'")
    result_3 = manager.handle_user_request(user_request_3)
    print(f"Result: {result_3}")
    # Expected: Success=True, title="Client Call", start_datetime for tomorrow 15:00

    # Invalid request: missing time
    user_request_4 = "Create a calendar event for tomorrow titled Follow Up"
    print(f"\nRequest: '{user_request_4}'")
    result_4 = manager.handle_user_request(user_request_4)
    print(f"Result: {result_4}")
    # Expected: Success=False, message about specifying time

    # Invalid request: invalid time format
    user_request_5 = "Create a calendar event for tomorrow at 30:00 titled Bad Time"
    print(f"\nRequest: '{user_request_5}'")
    result_5 = manager.handle_user_request(user_request_5)
    print(f"Result: {result_5}")
    # Expected: Success=False, message about invalid time format

    # Invalid request: not a calendar creation request
    user_request_6 = "Tell me the weather tomorrow"
    print(f"\nRequest: '{user_request_6}'")
    result_6 = manager.handle_user_request(user_request_6)
    print(f"Result: {result_6}")
    # Expected: Success=False, message about only creating calendar events

    # Invalid request: missing title
    user_request_7 = "Create a calendar event for tomorrow at 10 AM"
    print(f"\nRequest: '{user_request_7}'")
    result_7 = manager.handle_user_request(user_request_7)
    print(f"Result: {result_7}")
    # Expected: Success=False, message about specifying title

    # Valid request with explicit 24-hour time and different title keyword
    user_request_8 = "Make a meeting for tomorrow at 11:45 titled 'Team Standup'"
    print(f"\nRequest: '{user_request_8}'")
    result_8 = manager.handle_user_request(user_request_8)
    print(f"Result: {result_8}")
    # Expected: Success=True, title="Team Standup", start_datetime for tomorrow 11:45

    # Valid request with AM/PM and slightly different phrasing
    user_request_9 = "Add an appointment for tomorrow at 3 pm called 'Doctor Visit'"
    print(f"\nRequest: '{user_request_9}'")
    result_9 = manager.handle_user_request(user_request_9)
    print(f"Result: {result_9}")
    # Expected: Success=True, title="Doctor Visit", start_datetime for tomorrow 15:00
