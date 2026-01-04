import redis
import os
import json

REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) # decode_responses=False because we're handling JSON

def add_to_queue(guild_id: int, song_data: dict):
    """Adds a song to the end of a guild's queue."""
    r.rpush(f"queue:{guild_id}", json.dumps(song_data))

def add_to_front_of_queue(guild_id: int, song_data: dict):
    """Adds a song to the front of a guild's queue."""
    r.lpush(f"queue:{guild_id}", json.dumps(song_data))

def get_from_queue(guild_id: int):
    """Retrieves and removes the next song from a guild's queue."""
    song_json = r.lindex(f"queue:{guild_id}", 0)
    if song_json:
        return json.loads(song_json)
    return None

def remove_first_queue(guild_id: int):
    song_json = r.lpop(f"queue:{guild_id}")
    return json.loads(song_json)

def get_queue(guild_id: int):
    """Gets the entire queue for a guild without modifying it."""
    queue_json_list = r.lrange(f"queue:{guild_id}", 0, -1)
    return [json.loads(song_json) for song_json in queue_json_list]

def get_song_url(webpage_url: str):
    """Get song url if it was not expired"""
    return r.get(webpage_url)

def set_song_url(webpage_url: str, url: str, expired_at: int):
    """Set youtube song url with expiration date"""
    r.set(webpage_url, url, exat=expired_at)

def remove_from_queue(guild_id: int, index: int):
    """Removes a song from the queue at a specific index."""
    # To remove by index, we need to do a little trick.
    # We set the value at the index to a temporary unique value,
    # then use LREM to remove that value.
    # First, get the current length to ensure index is valid
    queue_len = r.llen(f"queue:{guild_id}")
    if not (-queue_len <= index < queue_len):
        return False # Index out of bounds

    # Get the item to be removed
    item_to_remove_json = r.lindex(f"queue:{guild_id}", index)
    if item_to_remove_json:
        # Remove all occurrences of this item (should be only one at this index)
        r.lrem(f"queue:{guild_id}", 0, item_to_remove_json)
        return True
    return False

def clear_queue(guild_id: int):
    """Clears the entire queue for a guild."""
    r.delete(f"queue:{guild_id}")

def set_repeat(guild_id: int, repeat: bool):
    r.set(f"repeat:{guild_id}", int(repeat))

def get_repeat(guild_id: int):
    return bool(r.get(f"repeat:{guild_id}"))

def publish_song_added(data: dict):
    """Publishes a song added event to a Redis pub/sub channel."""
    r.publish("song_added", json.dumps(data))

def publish_song_listened(data: dict):
    """Publishes a song listened event to a Redis pub/sub channel."""
    r.publish("song_listened", json.dumps(data))