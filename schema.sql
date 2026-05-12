create table public.users (
  user_id serial not null,
  username text not null,
  email text not null,
  password text not null,
  constraint users_pkey primary key (user_id),
  constraint users_email_key unique (email),
  constraint users_username_key unique (username)
) TABLESPACE pg_default;

create table public.movies (
  movie_id serial not null,
  movie_name text not null,
  year integer null,
  imdb_rating numeric(3, 1) null,
  constraint movies_pkey primary key (movie_id),
  constraint uq_movies_name_year unique (movie_name, year)
) TABLESPACE pg_default;

create table public.watched_movies (
  user_id integer not null,
  movie_id integer not null,
  watch_status boolean not null default false,
  rating numeric(3, 1) null,
  constraint watched_movies_pkey primary key (user_id, movie_id),
  constraint watched_movies_movie_id_fkey foreign KEY (movie_id) references movies (movie_id) on delete CASCADE,
  constraint watched_movies_user_id_fkey foreign KEY (user_id) references users (user_id) on delete CASCADE,
  constraint ck_watched_movies_rating_range check (
    (
      (rating is null)
      or (
        (rating >= (0)::numeric)
        and (rating <= (10)::numeric)
      )
    )
  )
) TABLESPACE pg_default;

create table public.actors (
  actor_id serial not null,
  actor_name text not null,
  constraint actors_pkey primary key (actor_id),
  constraint actors_actor_name_key unique (actor_name)
) TABLESPACE pg_default;

create table public.directors (
  director_id serial not null,
  name text not null,
  constraint directors_pkey primary key (director_id),
  constraint directors_name_key unique (name)
) TABLESPACE pg_default;

create table public.genres (
  genre_id serial not null,
  genre_name text not null,
  constraint genres_pkey primary key (genre_id),
  constraint genres_genre_name_key unique (genre_name)
) TABLESPACE pg_default;

create table public.movie_actors (
  movie_id integer not null,
  actor_id integer not null,
  constraint movie_actors_pkey primary key (movie_id, actor_id),
  constraint movie_actors_actor_id_fkey foreign KEY (actor_id) references actors (actor_id) on delete CASCADE,
  constraint movie_actors_movie_id_fkey foreign KEY (movie_id) references movies (movie_id) on delete CASCADE
) TABLESPACE pg_default;

create table public.movie_directors (
  movie_id integer not null,
  director_id integer not null,
  constraint movie_directors_pkey primary key (movie_id, director_id),
  constraint movie_directors_director_id_fkey foreign KEY (director_id) references directors (director_id) on delete CASCADE,
  constraint movie_directors_movie_id_fkey foreign KEY (movie_id) references movies (movie_id) on delete CASCADE
) TABLESPACE pg_default;

create table public.movie_genres (
  movie_id integer not null,
  genre_id integer not null,
  constraint movie_genres_pkey primary key (movie_id, genre_id),
  constraint movie_genres_genre_id_fkey foreign KEY (genre_id) references genres (genre_id) on delete CASCADE,
  constraint movie_genres_movie_id_fkey foreign KEY (movie_id) references movies (movie_id) on delete CASCADE
) TABLESPACE pg_default;