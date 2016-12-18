import httplib2
import sys

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

from settings import (
    CLIENT_SECRETS_FILE,
    YOUTUBE_READ_WRITE_SCOPE,
    MISSING_CLIENT_SECRETS_MESSAGE,
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION
)


def get_authenticated_service(args):

    flow = flow_from_clientsecrets(filename=CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_READ_WRITE_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def insert_broadcast(youtube, options):
    """
    Create a liveBroadcast resource and set its title, scheduled start time,
    scheduled end time, and privacy status.
    """

    insert_broadcast_response = youtube.liveBroadcasts().insert(
        part="snippet,status",
        body=dict(
            snippet=dict(
                title=options.broadcast_title,
                scheduledStartTime=options.start_time,
                scheduledEndTime=options.end_time
            ),
            status=dict(
                privacyStatus=options.privacy_status
            )
        )
    ).execute()

    snippet = insert_broadcast_response["snippet"]

    print("Broadcast '%s' with title '%s' was published at '%s'." % (
        insert_broadcast_response["id"], snippet["title"],
        snippet["publishedAt"]))

    return insert_broadcast_response["id"]


def insert_stream(youtube, options):
    """
    Create a liveStream resource and set its title, format, and ingestion type.
    This resource describes the content that you are transmitting to YouTube.
    """

    insert_stream_response = youtube.liveStreams().insert(
        part="snippet,cdn",
        body=dict(
            snippet=dict(
                title=options.stream_title
            ),
            cdn=dict(
                format="1080p",
                ingestionType="rtmp"
            )
        )
    ).execute()

    snippet = insert_stream_response["snippet"]

    print("Stream '%s' with title '%s' was inserted." % (
        insert_stream_response["id"], snippet["title"]))

    return insert_stream_response["id"]


def bind_broadcast(youtube, broadcast_id, stream_id):
    """
    Bind the broadcast to the video stream. By doing so, you link the video
    that you will transmit to YouTube to the broadcast that the video is for.
    """

    bind_broadcast_response = youtube.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id
    ).execute()

    print("Broadcast '%s' was bound to stream '%s'." % (
        bind_broadcast_response["id"],
        bind_broadcast_response["contentDetails"]["boundStreamId"]))

if __name__ == "__main__":
    argparser.add_argument("--broadcast-title", help="Broadcast title",
                           default="New Broadcast")
    argparser.add_argument("--privacy-status", help="Broadcast privacy status",
                           default="private")
    argparser.add_argument("--start-time", help="Scheduled start time",
                           default='2014-01-30T00:00:00.000Z')
    argparser.add_argument("--end-time", help="Scheduled end time",
                           default='2014-01-31T00:00:00.000Z')
    argparser.add_argument("--stream-title", help="Stream title",
                           default="New Stream")
    args = argparser.parse_args()

    youtube = get_authenticated_service(args)

    try:
        broadcast_id = insert_broadcast(youtube, args)
        stream_id = insert_stream(youtube, args)
        bind_broadcast(youtube, broadcast_id, stream_id)

    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
