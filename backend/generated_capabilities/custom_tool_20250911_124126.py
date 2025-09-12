
import datetime
import re
from typing import Dict, Any, Optional

class ReminderTool:
    """
    A specialized tool for creating reminders.

    This tool allows users to set reminders for specific times, with a focus
    on creating reminders for 'tomorrow'. It generates structured data
    representing the success or failure of the operation.

    It is designed to be used by an agent that can interpret user requests
    and call this tool's functions.
    """

    def __init__(self):
        """
        Initializes the ReminderTool.
        """
        pass

    def create_reminder_for_tomorrow(
        self,
        message: str,
        time_of_day: str = "9:00 AM"
    ) -> Dict[str, Any]:
        """
        Creates a reminder for tomorrow.

        This method takes a reminder message and an optional time of day
        (defaulting to 9:00 AM) and prepares the reminder details.
        Currently, this method does not interact with the system to set an
        actual notification. It returns structured data representing the
        planned reminder.

        Args:
            message: The content of the reminder.
            time_of_day: The time of day for the reminder (e.g., "10:30 AM", "2 PM", "14:00").
                         Defaults to "9:00 AM".

        Returns:
            A dictionary containing the status of the operation.
            On success, it includes:
            {
                "success": True,
                "message": "Reminder details successfully generated for tomorrow.",
                "reminder_details": {
                    "message": str,
                    "date": str, # YYYY-MM-DD format
                    "time": str  # HH:MM AM/PM format
                }
            }
            On failure, it includes:
            {
                "success": False,
                "message": "Error creating reminder: [error description]"
            }
        """
        if not message or not message.strip():
            return {
                "success": False,
                "message": "Error creating reminder: Reminder message cannot be empty."
            }

        try:
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            formatted_date = tomorrow.strftime("%Y-%m-%d")

            parsed_time_obj, formatted_time_str = self._parse_and_format_time(time_of_day)
            if parsed_time_obj is None:
                return {
                    "success": False,
                    "message": f"Error creating reminder: Invalid time format '{time_of_day}'. Please use formats like 'H:MM AM/PM', 'HH:MM AM/PM', or 'HH:MM' (24-hour clock)."
                }

            reminder_details = {
                "message": message.strip(),
                "date": formatted_date,
                "time": formatted_time_str,
            }

            return {
                "success": True,
                "message": "Reminder details successfully generated for tomorrow.",
                "reminder_details": reminder_details
            }
        except Exception as e:
            # Log the exception for debugging purposes if this were a real application
            # print(f"An unexpected error occurred: {e}")
            return {
                "success": False,
                "message": f"An unexpected error occurred while generating reminder details: {str(e)}"
            }

    def _parse_and_format_time(self, time_str: str) -> tuple[Optional[datetime.time], Optional[str]]:
        """
        Parses a time string and formats it into HH:MM AM/PM.

        Supports formats like:
        - "9:00 AM", "10:30 AM"
        - "2 PM", "3:15 PM"
        - "14:00", "09:30" (24-hour clock)

        Args:
            time_str: The time string to parse.

        Returns:
            A tuple containing:
            - A datetime.time object if parsing is successful, otherwise None.
            - The time string in "HH:MM AM/PM" format if successful, otherwise None.
        """
        time_str = time_str.strip().upper()

        # Regex for HH:MM AM/PM or H:MM AM/PM
        # Group 1: Hour (1-12), Group 2: Minute (00-59), Group 3: AM/PM
        am_pm_match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_str)
        if am_pm_match:
            hour, minute, period = am_pm_match.groups()
            try:
                hour = int(hour)
                minute = int(minute)
                if not (1 <= hour <= 12 and 0 <= minute <= 59):
                    return None, None

                dt_time = datetime.time(hour, minute)
                # Convert to standard HH:MM AM/PM string
                return dt_time, dt_time.strftime("%I:%M %p")
            except ValueError:
                return None, None

        # Regex for H AM/PM or HH AM/PM (assumes :00 for minutes)
        am_pm_no_minute_match = re.match(r"(\d{1,2})\s*(AM|PM)", time_str)
        if am_pm_no_minute_match:
            hour, period = am_pm_no_minute_match.groups()
            try:
                hour = int(hour)
                if not (1 <= hour <= 12):
                    return None, None
                dt_time = datetime.time(hour, 0)
                return dt_time, dt_time.strftime("%I:%M %p")
            except ValueError:
                return None, None

        # Regex for HH:MM (24-hour clock)
        # Group 1: Hour (00-23), Group 2: Minute (00-59)
        hour_minute_match = re.match(r"(\d{2}):(\d{2})", time_str)
        if hour_minute_match:
            hour, minute = hour_minute_match.groups()
            try:
                hour = int(hour)
                minute = int(minute)
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    return None, None

                dt_time = datetime.time(hour, minute)
                return dt_time, dt_time.strftime("%I:%M %p")
            except ValueError:
                return None, None

        return None, None


if __name__ == '__main__':
    # Example Usage
    tool = ReminderTool()

    print("--- Successful Reminders ---")
    result_success = tool.create_reminder_for_tomorrow(message="Call mom")
    print(f"Default time: {result_success}")

    result_success_specific_time = tool.create_reminder_for_tomorrow(
        message="Submit report",
        time_of_day="3:30 PM"
    )
    print(f"Specific AM/PM time: {result_success_specific_time}")

    result_success_24hr_time = tool.create_reminder_for_tomorrow(
        message="Team meeting",
        time_of_day="14:00"
    )
    print(f"24-hour time: {result_success_24hr_time}")

    result_success_noon = tool.create_reminder_for_tomorrow(
        message="Lunch break",
        time_of_day="12 PM"
    )
    print(f"Noon time: {result_success_noon}")

    result_success_midnight = tool.create_reminder_for_tomorrow(
        message="New Year's Eve",
        time_of_day="00:00"
    )
    print(f"Midnight time: {result_success_midnight}")

    print("\n--- Failed Reminders ---")
    result_failure_empty_message = tool.create_reminder_for_tomorrow(message="")
    print(f"Empty message: {result_failure_empty_message}")

    result_failure_whitespace_message = tool.create_reminder_for_tomorrow(message="   ")
    print(f"Whitespace message: {result_failure_whitespace_message}")

    result_failure_invalid_time_format_word = tool.create_reminder_for_tomorrow(
        message="Pick up dry cleaning",
        time_of_day="lunchtime"
    )
    print(f"Invalid time (word): {result_failure_invalid_time_format_word}")

    result_failure_invalid_time_format_numbers = tool.create_reminder_for_tomorrow(
        message="Project deadline",
        time_of_day="99:00"
    )
    print(f"Invalid time (numbers out of range): {result_failure_invalid_time_format_numbers}")

    result_failure_invalid_am_pm = tool.create_reminder_for_tomorrow(
        message="Invalid time format",
        time_of_day="3:70 PM"
    )
    print(f"Invalid time (minute out of range): {result_failure_invalid_am_pm}")

    result_failure_malformed_time = tool.create_reminder_for_tomorrow(
        message="Malformed time",
        time_of_day="2:30 PMish"
    )
    print(f"Malformed time: {result_failure_malformed_time}")

    result_failure_no_am_pm_24hr = tool.create_reminder_for_tomorrow(
        message="No AM/PM",
        time_of_day="15:30"
    )
    print(f"Valid 24-hour time: {result_failure_no_am_pm_24hr}")

    result_failure_invalid_24hr_hour = tool.create_reminder_for_tomorrow(
        message="Invalid 24hr hour",
        time_of_day="25:00"
    )
    print(f"Invalid 24hr hour: {result_failure_invalid_24hr_hour}")

    result_failure_invalid_24hr_minute = tool.create_reminder_for_tomorrow(
        message="Invalid 24hr minute",
        time_of_day="10:60"
    )
    print(f"Invalid 24hr minute: {result_failure_invalid_24hr_minute}")

    result_success_short_hour_pm = tool.create_reminder_for_tomorrow(
        message="Short hour PM",
        time_of_day="3 PM"
    )
    print(f"Short hour PM: {result_success_short_hour_pm}")

    result_success_short_hour_am = tool.create_reminder_for_tomorrow(
        message="Short hour AM",
        time_of_day="7 AM"
    )
    print(f"Short hour AM: {result_success_short_hour_am}")
