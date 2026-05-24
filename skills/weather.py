import requests
import threading
from datetime import datetime

# Weather module using Open-Meteo API (requires no API key)
# This module provides current time, date, live weather, and reminders.

class WeatherSkill:
    def __init__(self, default_city: str = "Nagpur"):
        self.default_city = default_city
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        print("[WEATHER] Weather module initialized.")

    def get_time(self) -> str:
        now = datetime.now()
        return f"It is {now.strftime('%I:%M %p')}, sir."

    def get_date(self) -> str:
        now = datetime.now()
        day = now.day
        if 11 <= day % 100 <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"Today is {now.strftime('%A')}, {day}{suffix} {now.strftime('%B %Y')}, sir."

    def set_reminder(self, time_str: str, message: str, callback=None) -> str:
        """
        Schedules a reminder. Supports:
          - 'in X minutes' / 'in X seconds'
          - 'at HH:MM AM/PM' or 'at HH:MM'
        Calls callback(message) when triggered; prints if no callback given.
        """
        delay = self._parse_delay(time_str)
        if delay is None:
            return f"I couldn't parse the time '{time_str}', sir. Try 'in 5 minutes' or 'at 5:30 PM'."

        def _fire():
            if callback:
                callback(f"Reminder, sir: {message}")
            else:
                print(f"\n[REMINDER] {message}")

        threading.Timer(delay, _fire).start()
        return f"Reminder set for {time_str}, sir. I'll let you know: '{message}'."

    def _parse_delay(self, time_str: str):
        """Returns seconds until the given time expression, or None if unparseable."""
        import re
        s = time_str.lower().strip()

        # 'in X minutes' or 'in X seconds' or 'in X hours'
        m = re.match(r"in\s+(\d+)\s*(minute|minutes|min|second|seconds|sec|hour|hours|hr)", s)
        if m:
            value = int(m.group(1))
            unit = m.group(2)
            if "sec" in unit:
                return value
            elif "min" in unit:
                return value * 60
            elif "hour" in unit or "hr" in unit:
                return value * 3600

        # 'at HH:MM AM/PM' or 'at HH AM/PM' or 'at HH:MM'
        m = re.match(r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", s)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2)) if m.group(2) else 0
            period = m.group(3)
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            now = datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                # next occurrence is tomorrow
                from datetime import timedelta
                target += timedelta(days=1)
            return (target - now).total_seconds()

        return None

    def _get_coordinates(self, city: str):
        # Uses Open-Meteo's geocoding API to convert a city name into latitude/longitude
        try:
            response = requests.get(
                self.geocoding_url,
                params={"name": city, "count": 1, "language": "en", "format": "json"},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if "results" not in data:
                return None
                
            result = data["results"][0]
            return {"lat": result["latitude"], "lon": result["longitude"], "name": result["name"]}
        except Exception as e:
            print(f"[WEATHER] Error fetching coordinates for {city}: {e}")
            return None

    def get_weather(self, city: str = None) -> str:
        # If no city is specified, default to Nagpur
        target_city = city if city else self.default_city
        
        # 1. Get coordinates for the city
        coords = self._get_coordinates(target_city)
        if not coords:
            return f"I'm sorry sir, I couldn't find the coordinates for {target_city}."
            
        try:
            # 2. Fetch current weather using the coordinates
            response = requests.get(
                self.base_url,
                params={
                    "latitude": coords["lat"],
                    "longitude": coords["lon"],
                    "current_weather": True
                },
                timeout=5
            )
            response.raise_for_status()
            weather_data = response.json()
            
            # Extract data from the response
            current_weather = weather_data.get("current_weather", {})
            temp = current_weather.get("temperature", "unknown")
            weather_code = current_weather.get("weathercode", -1)
            
            # Convert the numeric weather code into a human-readable condition
            condition = self._interpret_weather_code(weather_code)
            
            # Get current time and date to include in the response
            now = datetime.now()
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%A, %B %d")
            
            return f"It is currently {temp} degrees and {condition} in {coords['name']}, sir. The time is {time_str} on {date_str}."
            
        except Exception as e:
            print(f"[WEATHER] Error fetching weather data: {e}")
            return f"I encountered an error while fetching the weather for {target_city}, sir."

    def _interpret_weather_code(self, code: int) -> str:
        # Based on WMO weather interpretation codes
        if code == 0: return "clear sky"
        elif code in [1, 2, 3]: return "partly cloudy"
        elif code in [45, 48]: return "foggy"
        elif code in [51, 53, 55, 56, 57]: return "drizzling"
        elif code in [61, 63, 65, 66, 67]: return "raining"
        elif code in [71, 73, 75, 77]: return "snowing"
        elif code in [80, 81, 82]: return "showing rain showers"
        elif code in [85, 86]: return "showing snow showers"
        elif code in [95, 96, 99]: return "experiencing a thunderstorm"
        return "having mixed conditions"

# This block allows us to test the weather module independently
if __name__ == "__main__":
    weather_skill = WeatherSkill()
    
    print("\nTesting default city (Nagpur):")
    print(weather_skill.get_weather())
    
    print("\nTesting New York:")
    print(weather_skill.get_weather("New York"))
