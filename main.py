from custom_classes import MediaItem , Book , DVD, LibraryCollection
book1 = MediaItem("LOTR","Tolkien") 
movie = MediaItem("TENET", "Nolan")

print(book1.checkout())
print(movie.checkout())


book2 = Book("1984","orwell",320)
marvel = DVD("star wars","lucas",120)
marvel.checkout()
my_lib = LibraryCollection()
my_lib.add_item(book2)
my_lib.add_item(book1)
my_lib.add_item(movie)
my_lib.add_item(marvel)
print(my_lib.list_available())