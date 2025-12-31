import redis
import os
import json
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def create_constraints(self):
        with self._driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Song) REQUIRE s.url IS UNIQUE")

    def process_song_data(self, data):
        with self._driver.session() as session:
            session.execute_write(self._create_song_graph, data)

    def process_song_listened_data(self, data):
        with self._driver.session() as session:
            session.execute_write(self._create_song_listened_graph, data)

    @staticmethod
    def _create_song_graph(tx, data):
        query = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.name = $user_name
        ON MATCH SET u.name = $user_name

        MERGE (s:Song {url: $song_url})
        ON CREATE SET s.title = $song_title, s.duration = $song_duration, s.added_at = timestamp()
        ON MATCH SET s.title = $song_title, s.duration = $song_duration

        MERGE (g:Guild {id: $guild_id})
        ON CREATE SET g.name = $guild_name
        ON MATCH SET g.name = $guild_name
        
        MERGE (u)-[:ADDED]->(s)
        MERGE (s)-[:IN_GUILD]->(g)
        
        FOREACH (tag_name IN $song_tags |
            MERGE (t:Tag {name: tag_name})
            MERGE (s)-[:HAS_TAG]->(t)
        )
        """
        tx.run(query, **data)
        print(f"INFO: process_song_data with data: {data}")

    @staticmethod
    def _create_song_listened_graph(tx, data):
        query = """
        MERGE (s:Song {url: $song_url})

        MERGE (g:Guild {id: $guild_id})
        ON CREATE SET g.name = $guild_name
        ON MATCH SET g.name = $guild_name

        MERGE (s)-[:IN_GUILD]->(g)

        FOREACH (member IN $listened_members |
            MERGE (u:User {id: member.id})
            ON CREATE SET u.name = member.name
            ON MATCH SET u.name = member.name
            MERGE (u)-[:LISTENED]->(s)
        )
        """
        tx.run(query, **data)
        print(f"INFO: process_song_listened_data with data: {data}")


def main():
    # Exponential backoff for retries
    max_retries = 10
    retry_delay = 5  # seconds

    # Redis connection
    redis_conn = None
    for i in range(max_retries):
        try:
            redis_conn = redis.Redis(
                host=REDIS_HOST, 
                port=REDIS_PORT, 
                db=0
            )
            redis_conn.ping()
            print("INFO: Connected to Redis.")
            break
        except redis.exceptions.ConnectionError as e:
            print(f"WARN: Could not connect to Redis: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay *= 2
    if not redis_conn:
        print("CRITICAL: Could not connect to Redis after multiple retries. Exiting.")
        exit(1)

    # Neo4j connection
    neo4j_conn = None
    for i in range(max_retries):
        try:
            neo4j_conn = Neo4jConnection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            neo4j_conn.create_constraints()
            print("INFO: Connected to Neo4j and constraints are set.")
            break
        except Exception as e:
            print(f"WARN: Could not connect to Neo4j: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay *= 2
    if not neo4j_conn:
        print("CRITICAL: Could not connect to Neo4j after multiple retries. Exiting.")
        exit(1)


    pubsub = redis_conn.pubsub()
    pubsub.subscribe("song_added")
    pubsub.subscribe("song_listened")
    print("INFO: Subscribed to 'song_added' and 'song_listened' channels.")

    for message in pubsub.listen():
        if message['type'] == 'message':
            channel = message['channel'].decode('utf-8')
            data = json.loads(message['data'])
            
            if channel == 'song_added':
                neo4j_conn.process_song_data(data)
            elif channel == 'song_listened':
                neo4j_conn.process_song_listened_data(data)

if __name__ == "__main__":
    main()
