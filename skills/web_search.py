#let jarvis search web and wikipedia 

import wikipedia
from ddgs import DDGS

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

    #smart search
    def smart_search(self, query: str) -> str:
        q = query.lower()

        wiki_triggers = ["what is", "who is", "what are", "tell me about",
                         "explain", "define", "what was", "who was"]

        use_wiki = any(q.startswith(trigger) for trigger in wiki_triggers)

        if use_wiki:
            print(f"[SEARCH] Using Wikipedia for: {query}")
            return self.search_wiki(query)
        else:
            print(f"[SEARCH] Using DuckDuckGo for: {query}")
            return self.search_web(query)
    
    #standalone test
if __name__ == "__main__":
    searcher = WebSearcher()

    print("\n--- Wikipedia Test ---")
    print(searcher.search_wiki("artificial intelligence"))

    print("\n--- DuckDuckGo Test ---")
    print(searcher.search_web("latest news in technology"))

    print("\n--- Smart Search Test ---")
    print(searcher.smart_search("what is machine learning"))
    print()
    print(searcher.smart_search("best laptop 2026"))