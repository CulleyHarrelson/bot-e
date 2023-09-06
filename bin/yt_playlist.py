import os
import googleapiclient.discovery
from googleapiclient.errors import HttpError

# Set your API key or OAuth 2.0 credentials
API_KEY = os.environ["YOUTUBE_DATA_API_KEY"]

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)


def search_youtube_videos(search_phrase):
    try:
        # Perform the YouTube search
        request = youtube.search().list(
            q=search_phrase, type="video", part="id,snippet", maxResults=10
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


def create_youtube_playlist(playlist_title, video_ids):
    try:
        # Create a new playlist
        playlist_insert_response = (
            youtube.playlists()
            .insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": playlist_title,
                        "description": "Playlist created by API",
                    },
                    "status": {"privacyStatus": "public"},
                },
            )
            .execute()
        )

        playlist_id = playlist_insert_response["id"]

        # Add videos to the playlist
        for video_id in video_ids:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    },
                },
            ).execute()

        return playlist_id
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return None


# Example usage
search_phrase = "Headspace: The Mindfulness Guide for the Frazzled by Andy Puddicombe"
search_results = search_youtube_videos(search_phrase)
print(search_results)

video_ids = [result["videoId"] for result in search_results]
playlist_title = "bot-e Mindfulness Playlist"
playlist_id = create_youtube_playlist(playlist_title, video_ids)

if playlist_id:
    print(f"Playlist created with ID: {playlist_id}")
else:
    print("Failed to create the playlist.")
