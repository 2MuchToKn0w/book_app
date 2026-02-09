# Initialize models package and expose models
from .favorites import Favorite
from .users import User
from .reviews import Review
from .bookshelves import BookShelf
from .books_in_shelf import BookInShelf

__all__ = ["Favorite", "User", "Review", "BookShelf", "BookInShelf"]