from flask import Flask, render_template, request
from dotenv import find_dotenv, load_dotenv
import os
import json
from youtube_transcript_api import YouTubeTranscriptApi
import re
from openai import OpenAI

from langchain.document_loaders import YoutubeLoader


client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

load_dotenv(find_dotenv())
llm_model = "gpt-4"  # or gpt-4 or gpt-3.5-turbo


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form["videoUrl"]
        video_id = extract_video_id(video_url)
        try:
            transcript = fetch_transcript(video_id)
            timestamps = generate_timestamps(transcript)
            return render_template("index.html", timestamps=timestamps)
        except Exception as e:
            return render_template("index.html", error=str(e))

    return render_template("index.html", timestamps=None)


# def getstuf():
#     loader = YoutubeLoader.from_youtube_url(
#         "https://www.youtube.com/watch?v=IlS1aR_gfzs", add_video_info=True
#     )

#     # stuff = loader.load()

#     print(f"Lalalal==>{stuff[0]}")
#     return stuff


def extract_video_id(url):
    """
    Extracts the YouTube video ID from the URL.
    """
    # Regular expression for extracting the video ID
    regex = r"(youtu\.be\/|youtube\.com\/(?:watch\?v=|v\/|embed\/|watch\?.+&v=))((\w|-){11})"
    matches = re.search(regex, url)
    if matches:
        return matches.group(2)
    raise ValueError("Invalid YouTube URL")


# Example usage
# url = "https://www.youtube.com/watch?v=xT04yu1KUQw&ab_channel=CemEygi"
# video_id = extract_video_id(url)
# print(video_id)  # Outputs: dQw4w9WgXcQ


def fetch_transcript(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id=video_id)
    # format transcript

    formatted_transcript = format_timestamps(transcript)
    print(f"FORMATTED::: {formatted_transcript}")
    # just get the transcript and nothing else
    # for i in transcript:
    #     txt = i["text"]
    #     total_duration += float(i["duration"])
    #     text.append(txt)

    # return getstuf
    return formatted_transcript


def format_timestamps(json_data):
    formatted_timestamps = []

    for entry in json_data:
        text = entry.get("text", "")

        # Check if 'text' starts with '['
        if text.startswith("["):
            # Skip this entry
            continue

        # Convert 'start' from seconds to 'minutes:seconds' format
        minutes = int(entry["start"] // 60)
        seconds = int(entry["start"] % 60)
        formatted_time = f"{minutes:02}:{seconds:02}"

        # Combine formatted time with 'text'
        formatted_entry = f"{formatted_time} || {text}"
        formatted_timestamps.append(formatted_entry)

        # Join all formatted timestamps into a single string separated by newlines
    return "\n".join(formatted_timestamps)


def generate_timestamps(transcript):
    # Todo: maybe use langchain to make sure that in cases when the transcript's tokens exceed the
    # limit, we can bypass the token limit issues!!! )

    # final_transcript = format_timestamps()
    template = f"""
            As an AI skilled in analyzing YouTube video content, your task is to create up to 6 accurate timestamps from the provided transcript. Each timestamp should represent a distinct topic or main idea in the video.

            Guidelines for Timestamp Generation:
            1. Analyze the transcript without summarizing it.
            2. Ensure timestamps are well-spaced, each representing a complete topic or idea.
            3. Limit the total number of timestamps to 6.
            4. Titles for timestamps must be concise and clearly reflect the content of the segment.

            Timestamp Format:
            00:00 || [Title for the first segment]
            02:56 || [Title for the next segment]
            ... and so on.

            Based on the guidelines, generate the timestamps from this transcript:

            {transcript}

              
        """

    template_test = f"""
           You are an AI specialized in processing YouTube transcripts and generating accurate timestamps. You have the ability to understand video content structure and duration. 
           Your task is to create timestamps for the following YouTube transcript, ensuring that the timestamps correspond accurately to the content of the video. 

First, carefully analyze the entire transcript (do not provide the summary, only generate the timestamps). 
Then, create timestamps that are appropriately spaced, avoiding segments that are too short unless necessary for clarity.

Also make sure to transform the format of the transcript to:

```
10:15
going to wrap up the video here.
10:17
I hope you found this helpful.
10:18
And I know that these three things
10:20
were really
10:20
what helped me get better at programing
10:23
and feel confident
10:24
to write
10:24
pretty much any type of code,
10:26
any project and solve
10:27
any kind of problem.
10:29
I hope that they will help
10:30
```

Each timestamp should concisely summarize the topic or main point in that segment of the video. 
Ensure that all timestamps fit within the video's total duration and that the titles for each timestamp are brief and direct.



Format the timestamps as follows, including leading zeros:

        ```
        00:00 || Title for the first segment
        02:56 || Title for the second segment
        ```


Please generate the timestamps based on the content of this transcript:

{transcript} and the total duration of the video is about 

              
        """
    # Use OpenAI API to process transcript and generate timestamps
    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {
                "role": "system",
                "content": "You are a very knowledgeable Programmer and Youtuber",
            },
            {
                "role": "user",
                "content": f"{template}",
            },
        ],
        temperature=0.0
        # max_tokens=150,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    app.run(debug=True, port=5000)
