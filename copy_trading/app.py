from binance import future

# print(future.trade_history(symbol='BTCUSDT'))
# print(future.current_positions(symbol='XEMUSDT'))
# print(future.trade_history(symbol='BTCUSDT'))
# print(future.open_orders(symbol='XEMUSDT'))
# print(future.check_condetions_n_price(symbol='XEMUSDT',leverage=10,margin='isolated'))
# price=future.get_price(symbol='XEMUSDT')
# print(future.round_quantity(symbol='XEMUSDT',amount=15,price=price))
print(future.open_pos(symbol='XEMUSDT',amount=15, positionSide='SHORT',leverage=5,margin='isolated'))
