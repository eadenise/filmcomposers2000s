# Semantic Mapping of Early 2000s Movies and Soundtracks

Skills: Python, Data Serialisation, Webscraping, SPARQL, Protege

## About this project

This is a semantic framework that unifies film and music metadata through a purpose-built ontology centered on five
core concepts: Movie, Soundtrack, Track, Composer, and Genre, into a clear class hierarchy and define a rich property structure (for example, ‘hasSound-
track‘, ‘isTrackOf‘, and ‘performedBy‘) with precisely scoped domains, ranges,and characteristics such as functionality and transitivity.

## Problems this Ontology Solves"

Aside from automated logical inference, it solves the following:
1. Cross-source inconsistency<br>
    Wikidata and MusicBrainz use different identifiers and schemas for the same entities. The ontology acts as a unified layer — merging a film's metadata from Wikidata with its track listings from MusicBrainz into one consistent graph, so you can verify that a soundtrack actually belongs to the right movie.
2. Duplicate detection<br>
  MusicBrainz returns multiple release groups for the same soundtrack (regional editions, deluxe versions). Without the ontology, you'd have no principled way to know these are the same thing. The filtering logic (keeping only the earliest "official" release) reduced duplicates by over 75%.
3. Missing data identification<br>
    The ontology enforces that every Movie must have a soundtrack and composer. This constraint immediately exposed that "Frost/Nixon" and "How You Look to Me" had no MusicBrainz entries — something a plain database query might silently ignore.
4. Logical consistency checking <br>
    Pellet's reasoner could detect contradictions automaticallyFor example, the performedBy domain/range bug where Movies were being inferred as Tracks. Without formal reasoning, that kind of silent misclassification would corrupt query results undetected.

## Data Collection and Integration

Two main datasets: Wikidata and MusicBrainz API

Wikidata Query Service was used to retrieve basic film metadata, constructing SPARQL queries that returned triples for each film’s title, composer, release year, and genre.
Unfortunately, it does not include detailed soundtrack information, such as track listings and performing artists, I turned to MusicBrainz for those data.
Although MusicBrainz offers a SPARQL endpoint, it was nonfunctional for my needs, so I instead fetched the API’s JSON release-group responses
and converted them into RDF triples. In this way, each soundtrack release group became an RDF entity, from which I extracted track titles, music-genre classifications, 
and artist attributions, even when those artists differed from the composers.


## Ontology Design


| Class      | Asserted                                                                                                                                           | Inferred                                                                                               |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Movie      | Every movie has a sound-<br>track, at least one composer,<br>and at least one film genre.<br>(disjoint with Soundtrack)                            | Every soundtrack is the<br>soundtrack of at least one<br>Movie.                                        |
| Composer   | Each composer is linked to<br>one or more Movie or sound-<br>track via a composer role.<br>(disjoint with Artist)                                  | A movie or soundtrack is com-<br>posed by at least one com-<br>poser. A composer can be a<br>composer  |
| Genre      | Genre splits into two disjoint<br>subclasses: Film Genre and<br>Music Genre.                                                                       | Every<br>soundtrack<br>is<br>linked (by the inverse of<br>hasSoundtrack) to at least<br>one movie.<br> |
| Soundtrack | Every soundtrack contains<br>one or more tracks, has at<br>least one composer, and has<br>at least one music genre. (dis-<br>joint with movie)<br> |                                                                                                        |
| Track      | A or some tracks are part of<br>at least one Soundtrack.                                                                                           | Every track is performed by<br>at least one atist.                                                     |
| Artist     | An artist performs one or<br>more tracks (and is disjoint<br>from composer).                                                                       |                                                                                                        |


## T-box level of Axioms

• Any individual that hasGenreFilm must be a movie <br>
∃ hasGenreFilm.⊤ ⊑ Movie <br>
• Each Movie can have at most one hasSoundtrack connection. <br>
⊤ ⊑ ≤ 1 hasSoundtrack .Soundtrack <br>
• Each Soundtrack can be the soundtrack of at most one Movie. <br>
⊤ ⊑ ≤ 1 (isSoundtrackOf )− .Movie <br>
• If a Soundtrack has a Track, and that Track has a sub-track, the Soundtrack also has that sub-track <br>
hasTrack ◦ hasTrack ⊑ hasTrack
• No Movie can be its own soundtrack (irreflexivity). <br>
⊤ ⊑ ¬ ∃ hasSoundtrack .Self <br>
• The inverse of hasSoundtrackComposer is a sub-property of the inverse of composedFor.<br>
(hasSoundtrackComposer )− ⊑ (composedFor )−


## References
1] MusicBrainz, “MusicBrainz API / Rate Limiting,” MusicBrainz Wiki, Jan.
8, 2012. [Online]. Available: https://musicbrainz.org/doc/MusicBrainz API/Rate Limiting. Accessed: May 11, 2025. <br>
2] Colla, D., Goy, A., Leontino, M., & Magro, D. (2021). Wikidata support in the creation of rich semantic metadata for historical archives. 
Applied Sciences, 11(10), 4378. https://doi.org/10.3390/app11104378. Accessed: May 11, 2025.

