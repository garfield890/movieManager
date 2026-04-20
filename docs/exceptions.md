Exception 1: User is not able to login because their username or password is wrong.
If a user is not able to login, they will be redirected to create an account if their username is wrong or reset their password if their password is wrong.

Exception 2: Movie that a user wants to add is not in the movie database. 
If a user wants to add a movie that is not in the movie database, they will be able to manually add all the information about the movie themselves (title, genre, director, lead actors, etc).

Exception 3: Movie that a user wants to add has already been added.
If a user wants to add a movie that they have already added (will be checked with a database call), then the API should not allow them to add the movie and should say "Movie already added to your watched films." 

Exception 4: Actor name or director name is misspelled when user tries to search by actors or directors.
If a user misspells the name of an actor or director, the API should display an error saying "actor/director not found. Name may be misspelled."

Exception 5: User tries to query movies with rating when they have no movies with that rating.
If a user tries to query their movies by a rating when they have no movies with that rating, the API should show an error saying "No movies with hat rating. Try another rating."

Exception 6: User tries to query movies with genre when they have no movies with that genre.
If a user tries to query their movies with a genre when they have no movies matching that genre, the API should show an error saying "No movies with that genre. Try another genre."

Exception 7: User tries to query movies with release year when they have no movies that released in that year.
If a user tries to query their movies with a release year when they have no movies that released in that year, the API should show an error saying "No movies from that year. Try another year."

Exception 8: User tries to rate a movie that is not in their watched list. 
If a user tries to rate a movie that is not in their watched list, the API should ask them whether they want to add it to their watched list and then rate it.

Exception 9: User tries to add movie to custom list that is already in custom list.
If a user tries to add a movie to their custom lists when it is already in that custom list, the API should return an error saying "Movie already in list. Add another movie."

Exception 10: User tries to re-rate a movie that is already rated.
If a user tries to re-rate a movie that is already rated, the API should update the rating in the internal database.

Exception 11: User tries to get recommendations for movies when they have no/few movies in their watched movies list.
If a user tries to get recommendations for movies when they have no/few movies in their watched movies list, the API should return the most popular movies and say "Too few watched movies to generate personalized recommendations. Here are the most popular films of all time."

Exception 12: Recommendation returns a movie that is already in the user's watched list.
If a recommendation returns a movie that is already in the user's watched list, the API should remove that movie from the recommendation. Basically, the recommendation should be checked against the user's watched movies list.

Exception 13: No movies match the keyword the user is using to find movies.
If no movies match the keyword the user is using to find movies, the API should display an error saying "no movies match this search."