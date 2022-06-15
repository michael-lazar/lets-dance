import logging
import random
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from requests.exceptions import ConnectionError, HTTPError

from letsdance.core.client import put_board
from letsdance.core.constants import BOARD_TTL_DAYS, PUBLISH_BACKOFF_MAX_DAYS
from letsdance.core.models import Board, Peer

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


@scheduler.scheduled_job("interval", hours=1)
def expire_old_boards():
    """
    Expire any boards that haven't been updated in a while.
    """
    logger.info("Checking for old boards to expire.")
    min_age = timezone.now() - timedelta(days=BOARD_TTL_DAYS)
    count, _ = Board.objects.filter(last_modified__lt=min_age).delete()
    logger.info(f"Removed {count} boards due to TTL timeout.")


def broadcast_board(key: str) -> None:
    """
    Broadcast an uploaded board to peers in the server's realm.
    """
    board = Board.objects.get(key=key)

    peer_count = min(round(Peer.objects.all().count() * 0.5), 5)
    peers = Peer.objects.all().order_by("?")[:peer_count]
    logger.info(f"Sharing board {key} with {len(peers)} peer(s).")
    for peer in peers:
        job_id = f"publish:{key}"
        scheduler.add_job(
            publish_board,
            args=[board, peer.url],
            id=job_id,
            replace_existing=True,
            trigger="date",
        )
        logger.info(f"Scheduled job {job_id} with eta 0s.")


def publish_board(board: Board, url: str, backoff: int = 300):
    """
    Attempt to publish a board to a peer with exponential backoff.
    """
    logger.info(f"Publishing board {board} to peer {url}.")
    try:
        response = put_board(board, url)
    except (HTTPError, ConnectionError) as e:
        logger.info(f"Error publishing board: {e}")
        retry = True
    else:
        logger.info(f"Response code received: {response.status_code}")
        # Only retry for 5xx server errors
        retry = 500 <= response.status_code <= 600

    if retry:
        backoff = int(backoff + backoff * random.random())
        job_id = f"publish:{board.key}"
        if backoff < PUBLISH_BACKOFF_MAX_DAYS * 24 * 60 * 60:
            scheduler.add_job(
                publish_board,
                args=[board, url, backoff],
                id=job_id,
                trigger="date",
                run_date=timezone.now() + timedelta(seconds=backoff),
            )
            logger.info(f"Scheduled job {job_id} with eta {backoff}s.")
        else:
            logger.info(f"Backoff limit exceeded, giving up on job {job_id}")
