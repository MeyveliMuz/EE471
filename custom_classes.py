class MediaItem:
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.is_available = True  
        
    def checkout(self):
        if self.is_available:
            self.is_available = False
            return "Successful checkout"
        else:
            return "Already out"
        
    def return_item(self):
        self.is_available = True

    def __str__(self):
        if self.is_available:
            status = "Available"
        else:
            status = "Checked Out"
            
        return f"{self.title} by {self.author} [{status}]"
    
class Book(MediaItem):
     def __init__(self, title, author, page_count):
         super().__init__(title, author)
         self.page_count = page_count

     def __str__(self):
        base_info = super().__str__()
        return f"{base_info} - {self.page_count} pages"


class DVD(MediaItem):
    def __init__(self, title, author, duration):
        super().__init__(title, author)
        self.duration = duration

    def checkout(self):
        print("Handle with care: Do not scratch the disc.")
        return super().checkout()
class LibraryCollection:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def list_available(self):
        available_titles = []
        for item in self.items:
            if item.is_available:
                available_titles.append(item.title)
        return available_titles