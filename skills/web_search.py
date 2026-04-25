#let jarvis search web and wikipedia 

from PIL.Image import enum
from wikipedia import wikipedia
import wikipedia
from duckduckgo_search import DDGS

class WebSearcher:
    def __init__(self):
        print("[SEARCH] Web searcher initialized")

    #wikipedia
    def search_wiki(self, query: str) -> str:
        try:
            wikipedia.set_lang("en")
            
            results = wikipedia.search(query, results=3)
            
            if not results:
                return f"No wikipedia page found for {query}, sir."
            
            summary = wikipedia.summary(results[0], sentences=3, auto_suggest=False)
            return f"According to wikipedia... {summary}"
            
        except wikipedia.exceptions.DisambiguationError as e:
            try:
                summary = wikipedia.summary(e.options[0], sentences=2, auto_suggest=False)
                return f"According to Wikipedia: {summary}"
            except:
                return f"I found multiple results for {query} but couldn't narrow it down, sir."
        except wikipedia.exceptions.PageError:
            return f"I couldn't find a Wikipedia page for {query}, sir."

        except Exception as e:
            return f"Wikipedia search failed, sir. {e}"

    #to return summary of top results using duckduckgo
    def search_web(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))

            if not results: 
                return f"i couldnt find any results for {query}, sir."
            summary = f"here is what i found for {query}, sir."

            for i, r in enumerate(results[:2]):
                summary += f"{r['body']}"
            
            if len(summary) > 500:
                summary = summary[:500] + "..."

            return summary.strip()

        except Exception as e:
            return f"Web search failed, sir. {e}"