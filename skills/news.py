from ddgs import DDGS

class NewsSkill:
    def __init__(self):
        print("[NEWS] News module initialized.")

    def get_headlines(self, topic: str = None) -> str:
        """Fetches top 5 news headlines for a topic (or general top news)."""
        query = topic if topic else "top news today"
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=5))
            if not results:
                return "I couldn't find any news right now, sir."
            titles = [r["title"] for r in results]
            numbered = [f"{i + 1}: {t}" for i, t in enumerate(titles)]
            return "Here are today's top headlines, sir. " + ". ".join(numbered) + "."
        except Exception as e:
            print(f"[NEWS] Error: {e}")
            return f"News search failed, sir. {e}"

    def get_tech_news(self) -> str:
        return self.get_headlines("latest technology news today")

    def get_sports_news(self) -> str:
        return self.get_headlines("latest sports news today")

    def get_business_news(self) -> str:
        return self.get_headlines("latest business and finance news today")


if __name__ == "__main__":
    news = NewsSkill()
    print(news.get_headlines())
    print()
    print(news.get_tech_news())
