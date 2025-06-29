import rdflib
from rdflib.namespace import RDF, RDFS
from collections import defaultdict


# Loads film_soundtrack_2000s OWL ontology
g = rdflib.Graph()
g.parse('film_soundtrack_2000s.owl', format="xml")
print(f"Graph has {len(g)} statements.\n")

# Checks for movie details including movie, soundtrack, composer track and release daate
query_one= '''

PREFIX ma:    <http://www.semanticweb.org/film_soundtrack_2000s#>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 

SELECT ?movie ?movieLabel ?soundtrack ?soundtrackLabel ?track ?trackLabel ?composer ?composerLabel ?artist ?releaseYear 

WHERE {
    ?movie a ma:Movie .
    ?movie rdfs:label ?movieLabel .
    ?movie ma:releaseYear ?year

    ?soundtrack rdfs:label ?soundtrackLabel .
    ?track rdfs:label ?trackLabel . 
    ?composer rdfs:label ?composerLabel .

OPTIONAL{
?track    ma:performedBy   ?artist .
?artist   rdfs:label       ?artistLabel .
}
    
}
ORDER BY DESC(xsd:integer(?year))
LIMIT 100

'''

# Checks for film genre
query_two = '''
PREFIX ma:    <http://www.semanticweb.org/film_soundtrack_2000s#>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 

SELECT ?movieLabel ?genreLabel
WHERE {
  ?movie a ma:Movie .
  ?movie rdfs:label ?movieLabel .
  ?movie  ma:hasGenreFilm ?genre .
  ?genre rdfs:label ?genreLabel .
}
ORDER BY ?genreLabel ?movieLabel

'''

# Checks for soundtrack genre
query_three = '''
PREFIX ma:    <http://www.semanticweb.org/film_soundtrack_2000s#>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?soundtrackLabel ?musicGenreLabel
WHERE {
   ?soundtrack a ma:Soundtrack.
   ?soundtrack rdfs:label ?soundtrackLabel .
   ?soundtrack ma:hasGenreMusic ?genre_music .
   ?genre_music rdfs:label ?musicGenreLabel .
}

'''

query_four = '''

PREFIX ma:    <http://www.semanticweb.org/film_soundtrack_2000s#>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?soundtrackLabel ?sameGenreLabel
WHERE {
  ?soundtrack a ma:Soundtrack.
  ?soundtrack ma:hasSimilarMusicGenre ?sameGenre .
  ?soundtrack rdfs:label ?soundtrackLabel .
  ?sameGenre  rdfs:label ?sameGenreLabel .
}


'''

query_five = '''
PREFIX ma:   <http://www.semanticweb.org/film_soundtrack_2000s#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT  ?movieLabel ?soundtrackLabel ?genreLabel ?genre_filmLabel
WHERE {
  ?movie        a ma:Movie.
  ?movie        ma:hasGenreFilm ?genre_film.
  ?genre_film    rdfs:label      ?genre_filmLabel.
  ?movie        ma:hasSoundtrack ?soundtrack .
  ?movie        rdfs:label       ?movieLabel .
  ?soundtrack   ma:hasGenreMusic ?genre . 
  ?soundtrack    rdfs:label       ?soundtrackLabel .
  ?genre        rdfs:label        ?genreLabel .
  
  FILTER(lcase(str(?genreLabel)) = 'classical')

}
ORDER BY ?movieLabel
'''

# Shows movie soundtracks composed by Hans Zimmer
query_six = '''
PREFIX ma:   <http://www.semanticweb.org/film_soundtrack_2000s#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?movie ?movieLabel ?soundtrack ?soundtrackLabel ?composer ?composerLabel
WHERE {
?movie       a ma:Movie.
?movie     ma:hasSoundtrack ?soundtrack .
?soundtrack  rdfs:label    ?soundtrackLabel  
?composer  a  ma:Composer
?composer  rdfs:label    ?composerLabel  
 FILTER(lcase(str(?genreLabel)) = 'Hans Zimmer')

}


'''
# Run the sample query one
run_query = g.query(query_one)
group_labels = defaultdict(list)
for row in run_query:
    key = (row.movieLabel, row.soundtrackLabel, row.composerLabel)
    group_labels[key].append(row.trackLabel)

# Print each group with its tracks
for (movie, soundtrack, composer), tracks in group_labels.items():
    print(f"Movie:      {movie}")
    print(f"Soundtrack: {soundtrack}")
    print(f"Composer:   {composer}")
    print("Tracks:")
    for t in tracks:
        print("  -", t)
    print()



# Run the sample query five
print("\nTesting complete query:")
run_query = g.query(query_five)
for row in run_query:
    print(f"Movie:      {row.movieLabel}")
    print(f"Soundtrack: {row.soundtrackLabel}")
    print(f"Music Genre:      {row.genreLabel}")
    print(f"Film Genre {row.genre_filmLabel}")
    print()