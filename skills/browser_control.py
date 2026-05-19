import webbrowser
import urllib.parse

# The Browser Control module handles opening URLs and performing web searches.

class BrowserSkill:
    def __init__(self):
        print("[BROWSER] Browser Control module initialized.")

    def open_url(self, url: str) -> str:
        """Opens a specific URL in the default browser."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        print(f"[BROWSER] Opening {url}...")
        try:
            webbrowser.open(url)
            return f"Opening {url} in your browser, sir."
        except Exception as e:
            print(f"[BROWSER] Error opening URL: {e}")
            return f"I encountered an error trying to open the browser, sir: {e}"

    def search_google(self, query: str) -> str:
        """Performs a Google search in the default browser."""
        print(f"[BROWSER] Searching Google for: {query}")
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Searching Google for {query}, sir."
        except Exception as e:
            print(f"[BROWSER] Error searching Google: {e}")
            return "I was unable to perform the Google search, sir."

    def search_youtube(self, query: str) -> str:
        """Performs a YouTube search in the default browser."""
        print(f"[BROWSER] Searching YouTube for: {query}")
        try:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Searching YouTube for {query}, sir."
        except Exception as e:
            print(f"[BROWSER] Error searching YouTube: {e}")
            return "I was unable to search YouTube, sir."

if __name__ == "__main__":
    browser = BrowserSkill()
    print(browser.search_google("artificial intelligence"))
