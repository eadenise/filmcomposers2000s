import rdflib
from rdflib.graph import Graph, URIRef, Namespace, Literal
from rdflib.namespace import RDF, RDFS, XSD
from SPARQLWrapper import SPARQLWrapper, JSON, XML
import requests
import time

session = requests.Session()
session.headers.update({'User-Agent': 'FilmSoundtrackBot/1.0 (ec24145@qmul.ac.uk)'})

def mb_get(url, params=None):
    
    ''' 
    Wrapper for get against the MusicBrainz WS2 that:
        - Sleeps 1s between  requests.
        - On 503, reads header, sleeps, and retries.
        - Raises on any non-200 after retries.
    '''
    max_retries = 5
    for attempt in range(max_retries):
        r = session.get(url, params=params)
        if r.status_code == 200:
            time.sleep(1.0)                # always wait 1s
            return r
        elif r.status_code == 503:
            retry_after = int(r.headers.get('Retry-After', 1))
            print(f"Rate-limit hit. Sleeping {retry_after}s (attempt {attempt+1}/{max_retries})…")
            time.sleep(retry_after)
            continue
        else:
            # some other HTTP error
            r.raise_for_status()
    raise RuntimeError(f"Failed after {max_retries} attempts: {url} {params}")


name_space = Namespace('http://www.semanticweb.org/film_soundtrack_2000s#')


# Endpoint of WikiData dataset
sparql_wd = SPARQLWrapper('https://query.wikidata.org/sparql')

# Initialise RDF graph
g = Graph()
g.parse("film_soundtrack_2000s.owl", format="xml")  

g.bind("ma", name_space)

# Construct query using wikidata and ontology
query_one = '''
    PREFIX ma: <http://www.semanticweb.org/film_soundtrack_2000s#>
    PREFIX mo: <http://purl.org/ontology/mo/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX schema: <http://schema.org/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>


   CONSTRUCT {
    ?movie rdf:type ma:Movie .
    ?movie ma:releaseYear ?releaseYear .
    ?movie ma:hasGenreFilm   ?genre_film .
    ?movie rdfs:label ?movieLabel .


    ?soundtrack rdf:type ma:Soundtrack . 
    ?movie ma:hasSoundtrack ?soundtrack .
    ?movie ma:hasMovieComposer ?composer .
    ?soundtrack ma:hasGenreMusic  ?genre_music .
    ?soundtrack ma:hasSoundtrackComposer ?composer .
    ?soundtrack ma:hasTrack ?track . 

    
    ?composer rdf:type ma:Composer .
    ?composer ma:music ?composerMBID .
    ?composer rdfs:label ?composerLabel .
    
    ?genre_film rdf:type ma:Genre_Film .
    ?genre_film rdfs:label ?genre_film_label .

    ?genre_music rdf:type ma:Genre_Music . 
    ?genre_music rdfs:label ?genre_music_label .

    ?track rdfs:type ma:Track  .
    ?artist rdf:type ma:Artist . 
    ?track ma:performedBy ?artist . 

    }

    WHERE {
    
    ?movie wdt:P31 wd:Q11424 .         
    ?movie wdt:P86 ?composer .         
    ?composer wdt:P106 wd:Q1415090 . 
    
    ?movie rdfs:label ?movieLabel .
    ?composer rdfs:label ?composerLabel .

    ?movie wdt:P577 ?releaseDate .
    BIND(YEAR(?releaseDate) AS ?releaseYear)
    FILTER(?releaseYear >= 2000 && ?releaseYear <= 2010)
  
    OPTIONAL{
    ?movie wdt:P136 ?genre_film .  
    ?genre_film rdfs:label ?genre_film_label .
    FILTER(LANG(?genre_film_label) = "en") 
    }

    OPTIONAL { 
    ?composer wdt:P434 ?composerMBID . 
    }

    FILTER(LANG(?movieLabel) = "en")
    FILTER(LANG(?composerLabel) = "en")


    }

    LIMIT 200

  '''

sparql_wd.setQuery(query_one)
sparql_wd.setReturnFormat(XML)
sparql_wd.addCustomHttpHeader("User-Agent", "FilmSoundtrackBot/1.0 (ec24145@qmul.ac.uk)")
data = sparql_wd.query().convert()

if isinstance(data, Graph):
    for s, p, o in data:
        g.add((s, p, o))
    print(f"Wikidata CONSTRUCT: {len(g)} triples in graph")



# Create movie-composer pairs
pairs = []

# Query to extract movie-composer pairs from the graph and relabels them
select_query_two = '''
PREFIX ma: <http://www.semanticweb.org/film_soundtrack_2000s#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?movie ?movieLabel ?composer ?composerLabel
WHERE {
    ?movie a ma:Movie .
    ?movie  ma:hasMovieComposer ?composer .
    ?movie rdfs:label ?movieLabel .
    ?composer rdfs:label ?composerLabel .
}
'''
for row in g.query(select_query_two):
    pairs.append((row.movie, row.movieLabel, row.composer, row.composerLabel))

# build MusicBrainz search

for movie_uri, movie_label, composer_uri, composer_label in pairs:

    # secondary soundtrack
    query_mc = f'release:"{movie_label}" AND artist:"{composer_label}" AND secondarytype:Soundtrack'
    # print(f"\n>> Searching MusicBrainz: {query_mc}")
    mb_url = 'https://musicbrainz.org/ws/2/release-group/'
    params = {'query': query_mc, 'fmt': 'json', 'limit': 5}

    # fetch release-groups
    for attempt in range(3):
        r = mb_get(mb_url, params=params)
        if r.status_code == 503:
            time.sleep(2 ** attempt)
            continue
        break

    if r.status_code != 200:
        print(f"ERROR {r.status_code} on search for {movie_label}: {r.text[:200]}")
        continue

    mb_data = r.json()
    rgs = mb_data.get('release-groups', [])
    # print(f" → Found {len(rgs)} release-groups")

    # process each release-group
    for rg in rgs:
        rg_id = rg['id']
        title  = rg.get('title', movie_label + " Soundtrack")
        soundtrack_uri = URIRef(name_space + 'soundtrack_' + rg_id)
        g.add((soundtrack_uri, RDF.type, name_space.Soundtrack))
        g.add((soundtrack_uri, RDFS.label, Literal(title, lang='en')))
        g.add((movie_uri, name_space.hasSoundtrack, soundtrack_uri))

        # movie composer
        g.add((movie_uri,    name_space.hasMovieComposer, composer_uri))
        # soundtrack composer
        g.add((soundtrack_uri, name_space.hasSoundtrackComposer, composer_uri))
       
        # get full RG details
        rg_url = f"https://musicbrainz.org/ws/2/release-group/{rg_id}"
        rg_params = {'inc': 'releases+artist-credits+genres', 'fmt': 'json'}
        for attempt in range(3):
            rg_r = mb_get(rg_url, params=rg_params)
            if rg_r.status_code == 503:
                time.sleep(2 ** attempt)
                continue
            break

        if rg_r.status_code != 200:
            print(f"ERROR {rg_r.status_code} on RG details for {rg_id}: {rg_r.text[:200]}")
            continue
        rg_data = rg_r.json()

        # add genres
        for genre_data in rg_data.get('genres', []):
            name = genre_data['name']
            uri  = URIRef(name_space + 'genre_music_' + name.replace(' ', '_'))
            g.add((uri, RDF.type, name_space.Genre_Music))
            g.add((uri, RDFS.label, Literal(name)))
            g.add((soundtrack_uri, name_space.hasGenreMusic, uri))

        # choose the "best" release where it has an "official" status
        releases = rg_data.get('releases', [])
        if not releases:
            continue

        # filter for official
        official = [r for r in releases if r.get('status')=='Official']
        candidates = official or releases

        # find release with most tracks
        best = None
        best_count = -1
        for rel in candidates:
            rel_id = rel['id']
            rel_url = f"https://musicbrainz.org/ws/2/release/{rel_id}"
            rel_params = {'inc': 'recordings+artist-credits', 'fmt': 'json'}
            rel_r = mb_get(rel_url, params=rel_params)
            if rel_r.status_code != 200:
                continue
            rel_data = rel_r.json()
            # sum all track counts
            cnt = sum(m.get('track-count', 0) for m in rel_data.get('media', []))
            if cnt > best_count:
                best_count, best = (cnt, rel_data)

        if not best:
            continue

        # add tracks & performers
        for medium in best.get('media', []):
            for track in medium.get('tracks', []):
                tid = track['id']
                t_uri = URIRef(name_space + 'track_' + tid)
                if (soundtrack_uri, name_space.hasTrack, t_uri) not in g:
                    g.add((t_uri, RDF.type, name_space.Track))
                    g.add((t_uri, RDFS.label, Literal(track.get('title', 'Unknown'))))
                    g.add((soundtrack_uri, name_space.hasTrack, t_uri))

                    for ac in track.get('artist-credit', []):
                        if 'artist' in ac:
                            art = ac['artist']
                            a_uri = URIRef(name_space + 'artist_' + art['id'])
                            g.add((a_uri, RDF.type, name_space.Artist))
                            g.add((a_uri, RDFS.label, Literal(art.get('name', 'Unknown'))))
                            g.add((t_uri, name_space.performedBy, a_uri))

# Serialise 
g.serialize(destination="film_soundtrack_2000s.owl", format="xml")
print(f"Graph updated and saved with {len(g)} triples")
