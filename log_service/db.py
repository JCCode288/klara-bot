from neo4j import GraphDatabase

class Neo4j:
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
        WITH datetime().year + "-W" + datetime().week AS current_week

        MERGE (u:User {id: $user_id})
        ON CREATE SET u.name = $user_name
        ON MATCH SET u.name = $user_name

        MERGE (s:Song {url: $song_url})
        ON CREATE SET s.title = $song_title, s.duration = $song_duration, s.added_at = timestamp()
        ON MATCH SET s.title = $song_title, s.duration = $song_duration

        MERGE (g:Guild {id: $guild_id})
        ON CREATE SET g.name = $guild_name
        ON MATCH SET g.name = $guild_name
        
        MERGE (u)-[r:ADDED {bucket: current_week}]->(s)
        ON CREATE SET r.count = 1, r.first_added = timestamp()
        ON MATCH SET r.count = r.count + 1, r.last_added = timestamp()

        MERGE (u)-[:IN_GUILD]->(g)
        
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
        WITH datetime().year + "-W" + datetime().week AS current_week

        MERGE (s:Song {url: $song_url})
        ON CREATE SET s.title = $song_title, s.added_at = timestamp(), s.url = $song_url
        ON MATCH SET s.title = $song_title

        MERGE (g:Guild {id: $guild_id})
        ON CREATE SET g.name = $guild_name
        ON MATCH SET g.name = $guild_name

        FOREACH (member IN $listened_members |
            MERGE (u:User {id: member.id})
            ON CREATE SET u.name = member.name
            ON MATCH SET u.name = member.name
           
            MERGE (u)-[r:LISTENED {bucket: current_week}]->(s)
            ON CREATE SET r.count = 1, r.first_listened = timestamp()
            ON MATCH SET r.count = r.count + 1, r.last_listened = timestamp()

            MERGE (u)-[:IN_GUILD]->(g)
        )
        """
        tx.run(query, **data)
        print(f"INFO: process_song_listened_data with data: {data}")

