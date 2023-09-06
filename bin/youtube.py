import os
import googleapiclient.discovery
from googleapiclient.errors import HttpError

# Set your API key or OAuth 2.0 credentials
YOUTUBE_API_KEY = os.environ["YOUTUBE_DATA_API_KEY"]

# Initialize the YouTube Data API client


def search_youtube_videos(search_phrase):
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=YOUTUBE_API_KEY
    )
    try:
        # Perform the YouTube search
        request = youtube.search().list(
            q=search_phrase, type="video", part="id,snippet", maxResults=1
        )

        response = request.execute()

        # Construct the list of dictionaries
        results = []
        for item in response.get("items", []):
            result = {
                "videoId": item["id"]["videoId"],
                "thumbnailUrl": item["snippet"]["thumbnails"]["default"]["url"],
                "title": item["snippet"]["title"],
            }
            results.append(result)

        return results
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return []


# Example usage
search_phrase = "Headspace: The Mindfulness Guide for the Frazzled by Andy Puddicombe"
search_results = search_youtube_videos(search_phrase)
print(search_results)
