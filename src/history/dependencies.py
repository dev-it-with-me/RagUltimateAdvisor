from .repositories import HistoryRepository
from .services import HistoryService


def get_history_repository() -> HistoryRepository:
    return HistoryRepository()


def get_history_service() -> HistoryService:
    return HistoryService(repository=get_history_repository())
