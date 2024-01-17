import argparse
import logging

from boardgamegeek.api import HOT_ITEM_CHOICES, BGGClient

log = logging.getLogger("boardgamegeek")
log_fmt = "[%(levelname)s] %(message)s"


def brief_game_stats(game):
    # XXX: Is it needed?
    desc = '''"{}",{},{}-{},{},{},{},{},"{}","{}"'''.format(
        game.name,
        game.year,
        game.min_players,
        game.max_players,
        game.playing_time,
        game.rating_average,
        game.rating_average_weight,
        game.users_rated,
        " / ".join(game.categories).lower(),
        " / ".join(game.mechanics).lower(),
    )

    log.info(desc)
    log.info(f"Name        : {game.name}")
    log.info(f"Categories  : {game.categories}")
    log.info(f"Mechanics   : {game.mechanics}")
    log.info(f"Players     : {game.min_players}-{game.max_players}")
    log.info(f"Age         : {game.min_age}")
    log.info(f"Play time   : {game.playing_time}")
    log.info(f"Game weight : {game.rating_average_weight}")
    log.info(f"Score       : {game.rating_average}")
    log.info(f"Votes       : {game.users_rated}")


def main():
    p = argparse.ArgumentParser(prog="boardgamegeek")

    p.add_argument("-u", "--user", help="Query by user name")
    p.add_argument("-g", "--game", help="Query by game name")
    p.add_argument(
        "--most-recent",
        help="get the most recent game when querying by name (default)",
        action="store_true",
    )
    p.add_argument(
        "--most-popular",
        help="get the most popular (top ranked) game when querying by name",
        action="store_true",
    )

    p.add_argument("-i", "--id", help="Query by game id", type=int)
    p.add_argument("--game-stats", help="Return brief statistics about the game")
    p.add_argument("-G", "--guild", help="Query by guild id")
    p.add_argument("-c", "--collection", help="Query user's collection")
    p.add_argument("-p", "--plays", help="Query user's play list")
    p.add_argument("-P", "--plays-by-game", help="Query a game's plays")
    p.add_argument(
        "-H", "--hot-items", help="List all hot items by type", choices=HOT_ITEM_CHOICES
    )
    p.add_argument("-S", "--search", help="search and return results")
    p.add_argument("--debug", action="store_true")
    p.add_argument(
        "--retries",
        help="number of retries to perform in case of timeout or API HTTP 202 code",
        type=int,
        default=5,
    )
    p.add_argument("--timeout", help="Timeout for API operations", type=int, default=10)

    args = p.parse_args()

    # configure logging
    if args.debug:
        log_level = logging.DEBUG
    else:
        # make requests shush
        logging.getLogger("requests").setLevel(logging.WARNING)
        log_level = logging.INFO

    log.setLevel(log_level)
    stdout = logging.StreamHandler()
    stdout.setLevel(log_level)

    fmt = logging.Formatter(log_fmt)
    stdout.setFormatter(fmt)
    log.addHandler(stdout)

    def progress_cb(items, total):
        log.debug(f"fetching items: {items*100/total}% complete")

    if not any(
        [
            args.user,
            args.game,
            args.id,
            args.guild,
            args.collection,
            args.plays,
            args.plays_by_game,
            args.hot_items,
            args.search,
        ]
    ):
        p.error("no action specified!")

    bgg = BGGClient(timeout=args.timeout, retries=args.retries)

    if args.user:
        user = bgg.user(args.user, progress=progress_cb)
        user._format(log)

    # query by game id
    if args.id:
        game = bgg.game(game_id=args.id, comments=True)
        game._format(log)

    # query by game name
    if args.game:
        # fetch the most popular
        if args.most_popular:
            game = bgg.game(args.game, choose="best-rank", comments=True)
        else:
            # fetch the most recent one
            game = bgg.game(args.game, choose="recent", comments=True)
        game._format(log)

    if args.game_stats:
        game = bgg.game(args.game_stats)
        brief_game_stats(game)

    if args.guild:
        guild = bgg.guild(args.guild, progress=progress_cb)
        guild._format(log)

    if args.collection:
        collection = bgg.collection(args.collection, versions=True)
        collection._format(log)

    if args.plays:
        plays = bgg.plays(name=args.plays, progress=progress_cb)
        plays._format(log)

    if args.plays_by_game:
        try:
            game_id = int(args.plays_by_game)
        except ValueError:
            game_id = bgg.get_game_id(args.plays_by_game)

        plays = bgg.plays(game_id=game_id, progress=progress_cb)
        plays._format(log)

    if args.hot_items:
        hot_items = bgg.hot_items(args.hot_items)
        for item in hot_items:
            item._format(log)
            log.info("")

    if args.search:
        results = bgg.search(args.search)
        for r in results:
            r._format(log)
            log.info("")


if __name__ == "__main__":
    main()
