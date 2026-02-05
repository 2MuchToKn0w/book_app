import httpx
import re

BASE_URL = "https://openlibrary.org"


class OpenLibraryService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def search_books(self, query: str, limit: int = 10, offset: int = 0):
        """
        Performs a book search in Open Library using the constructed search query
        """
        response = await self.client.get(
            "/search.json",
            params={"q": query, "limit": limit, "offset": offset}
        )
        response.raise_for_status()
        return response.json()


    async def get_book_by_edition(self, edition_id: str) -> dict | None:
        """
        Returns detailed information about a book by edition OLID
        """

        # Get edition
        try:
            edition_resp = await self.client.get(f"/books/{edition_id}.json")
            edition_resp.raise_for_status()
            edition = edition_resp.json()
        except httpx.HTTPError:
            return None

        # Title, ISBN, pages, publisher
        title = edition.get("title")

        isbn = edition.get("isbn_10", []) + edition.get("isbn_13", [])

        pages = edition.get("number_of_pages")

        publishers = edition.get("publishers") or []

        # Language
        languages = [
            lang["key"].split("/")[-1]
            for lang in edition.get("languages", [])
            if "key" in lang
        ]

        # Publication year
        year = None
        publish_date = edition.get("publish_date")
        if publish_date:
            match = re.search(r"\d{4}", publish_date)
            if match:
                year = int(match.group())

        # Cover
        cover_url = None
        covers = edition.get("covers")
        if covers:
            cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg"

        # Work info: work_olid, description, subjects
        work_olid = None
        description = None
        subjects = []

        works = edition.get("works")
        if works:
            work_key = works[0].get("key")
            if work_key:
                work_olid = work_key.split("/")[-1]

                try:
                    work_resp = await self.client.get(f"{work_key}.json")
                    work_resp.raise_for_status()
                    work = work_resp.json()

                    description = work.get("description")
                    if isinstance(description, dict):
                        description = description.get("value")

                    subjects = work.get("subjects") or []
                except httpx.HTTPError:
                    pass

        # Authors
        authors: list[str] = []

        for a in edition.get("authors", []):
            author_key = a.get("key")
            if not author_key:
                continue

            try:
                author_resp = await self.client.get(f"{author_key}.json")
                author_resp.raise_for_status()
                author = author_resp.json()
                if "name" in author:
                    authors.append(author["name"])
            except httpx.HTTPError:
                continue

        # Return normalized dict
        return {
            "work_olid": work_olid,
            "title": title,
            "authors": authors or None,
            "description": description,
            "language": languages or None,
            "year": year,
            "isbn": isbn or None,
            "pages": pages,
            "cover_url": cover_url,
            "subject": subjects or None,
            "publisher": publishers or None,
        }


    async def get_book_by_work(self, work_id: str) -> dict | None:
        """
        Returns detailed information about a book by work OLID
        """

        try:
            resp = await self.client.get(f"/works/{work_id}.json")
            resp.raise_for_status()
            work = resp.json()
        except httpx.HTTPError:
            return None

        # Title
        title = work.get("title")

        # Authors
        authors = []
        for a in work.get("authors", []):
            author_key = a.get("author", {}).get("key")
            if author_key:
                try:
                    author_resp = await self.client.get(f"{author_key}.json")
                    author_resp.raise_for_status()
                    author = author_resp.json()
                    authors.append(author.get("name"))
                except httpx.HTTPError:
                    continue

        # Publication year
        year = work.get("first_publish_date")
        if year:
            match = re.search(r"\d{4}", year)
            if match:
                year = int(match.group())
        else:
            year = None

        # Cover
        cover_url = None
        covers = work.get("covers")
        if covers:
            cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg"

        return {
            "work_olid": work_id,
            "title": title,
            "authors": authors or None,
            "year": year,
            "cover_url": cover_url,
        }