from centralized_API_backend.models import AsuraScans, LightNovelPub, AllBooks, Genre

def migrate_genres_for_model(model, name):
    counter = 1
    for novel in model.objects.all():
        genre_names = novel.genres
        # Remove any existing genres first
        novel.new_genres.clear()
        for genre_name in genre_names:
            genre, created = Genre.objects.get_or_create(name=genre_name)
            # print(f"Pushed {genre} to MongoDB collection!")
            novel.new_genres.add(genre)

        print(f"{counter}. {name}: {novel.title} successfully migrated")
        counter += 1
        
        # novel.genres = []
        # novel.save()

migrate_genres_for_model(AsuraScans, "AsuraScans")
migrate_genres_for_model(LightNovelPub, "LightNovelPub")
migrate_genres_for_model(AllBooks, "AllBooks")