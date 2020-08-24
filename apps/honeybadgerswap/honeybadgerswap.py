import asyncio
import logging

from honeybadgermpc.mpc import TaskProgramRunner
from honeybadgermpc.preprocessing import (
    PreProcessedElements as FakePreProcessedElements,
)

from honeybadgermpc.progs.fixedpoint import FixedPoint
from honeybadgermpc.progs.mixins.share_arithmetic import (
    BeaverMultiply,
    BeaverMultiplyArrays,
    MixinConstants,
)

config = {
    MixinConstants.MultiplyShareArray: BeaverMultiplyArrays(),
    MixinConstants.MultiplyShare: BeaverMultiply(),
}


async def eth_to_token(
    ctx,
    init_eth_pool: FixedPoint,
    init_token_pool: FixedPoint,
    eth_to_exchange: FixedPoint,
):
    fee = await eth_to_exchange.div(500)
    k = await (init_eth_pool * init_token_pool)
    new_eth_pool = init_eth_pool + eth_to_exchange
    new_token_pool = await k.div(new_eth_pool - fee)
    tokens_to_receive = init_token_pool - new_token_pool

    return (tokens_to_receive, new_eth_pool, new_token_pool)


async def token_to_eth(
    ctx,
    init_eth_pool: FixedPoint,
    init_token_pool: FixedPoint,
    tokens_to_exchange: FixedPoint,
):
    fee = await tokens_to_exchange.div(500)
    k = await (init_eth_pool * init_token_pool)
    new_token_pool = init_token_pool + tokens_to_exchange
    new_eth_pool = await k.div(new_token_pool - fee)
    eth_to_receive = init_eth_pool - new_eth_pool

    return (eth_to_receive, new_eth_pool, new_token_pool)


def create_secret_share(ctx, x):
    return FixedPoint(ctx, ctx.Share(x * 2 ** 32) + ctx.preproc.get_zero(ctx))


def create_clear_share(ctx, x):
    return FixedPoint(ctx, ctx.Share(x * 2 ** 32))


async def prog(ctx):
    init_eth_pool = create_clear_share(ctx, 10)
    init_token_pool = create_clear_share(ctx, 500)
    eth_to_exchange = create_clear_share(ctx, 1)
    tokens, new_eth_pool, new_token_pool = await eth_to_token(
        ctx, init_eth_pool, init_token_pool, eth_to_exchange
    )

    print("Initial ETH Pool: {}".format(await init_eth_pool.open()))
    print("Initial Token Pool: {}".format(await init_token_pool.open()))
    print("k: {}".format(await init_eth_pool.open() + await init_token_pool.open()))
    print("Tokens received: {}".format(await tokens.open()))
    print("New eth pool: {}".format(await new_eth_pool.open()))
    print("New token pool: {}".format(await new_token_pool.open()))


async def honey_badger_swap():
    n, t = 4, 1
    k = 10000
    pp = FakePreProcessedElements()
    pp.generate_zeros(k, n, t)
    pp.generate_triples(k, n, t)
    pp.generate_bits(k, n, t)
    program_runner = TaskProgramRunner(n, t, config)
    program_runner.add(prog)
    results = await program_runner.join()
    return results


def main():
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(honey_badger_swap())


if __name__ == "__main__":
    main()
    print("HoneyBadgerSwaped!")
