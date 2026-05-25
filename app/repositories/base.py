"""Shared repository infrastructure."""

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Base class for all repositories.

    A repository encapsulates database access for a single aggregate: it
    runs queries and stages changes (insert/delete) on the session, but
    it never commits. The transaction boundary is owned by the service
    layer, so several repository calls can be combined into one atomic
    unit of work.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
