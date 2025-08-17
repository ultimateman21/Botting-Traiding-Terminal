from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX, INVEST_GRPC_API
from tinkoff.invest.utils import decimal_to_quotation, quotation_to_decimal, money_to_decimal
from tinkoff.invest import Client
from tinkoff.invest.schemas import MoneyValue, CandleInterval, CandleSource, OrderDirection, OrderType, InstrumentType, \
     InstrumentStatus, InstrumentIdType,  AssetsRequest, GetAssetFundamentalsRequest, MarketDataRequest, SubscribeCandlesRequest, \
     SubscriptionAction, CandleInstrument, SubscriptionInterval, OrderStateStreamRequest, OrderExecutionReportStatus, GetOrderPriceRequest

from tinkoff.invest.typedefs import AccountId


from PyQt6.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, Qt

from decimal import Decimal
from PyQt6.QtCore import QLocale
from typing import Literal, Callable
from pandas import DataFrame
from datetime import datetime, timezone
from math import ceil
from functools import partial

import pandas as pd
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')

# Настройки для отображения всех строк и столбцов
pd.set_option('display.max_rows', None)  # Показать все строки
pd.set_option('display.max_columns', None)  # Показать все столбцы
pd.set_option('display.width', None)  # Автоподбор ширины
pd.set_option('display.max_colwidth', None)  # Показать полное содержимое ячеек


class Tinkoff:
    def __init__(self, token: str):
        self.token = token
        self.target = INVEST_GRPC_API_SANDBOX
        self.info = [self.token, self.target]

        self.assets = self.Assets(self)
        self.sandbox = self.SandBox(self)
        self.shares = self.Shares(self)

    def get_accounts(self):
        with Client(token=self.token, target=self.target) as client:
            response = client.users.get_accounts()
        return response.accounts

    def get_accounts_ids(self):
        return {acc.id: {'name': acc.name} for acc in self.get_accounts()}

    def get_candles(self, uid: str, interval: Literal[1, 3, 5, 15, 30, 60, 120, 240, 'D', 'W', 'M'],
                    from_: int, to_: int, purpose: Literal['single', 'multiple']):
        try:
            match = {1: [CandleInterval.CANDLE_INTERVAL_1_MIN, 2400], 3: [CandleInterval.CANDLE_INTERVAL_3_MIN, 750],
                     5: [CandleInterval.CANDLE_INTERVAL_5_MIN, 2400], 15: [CandleInterval.CANDLE_INTERVAL_15_MIN, 2400],
                     30: [CandleInterval.CANDLE_INTERVAL_30_MIN, 1200], 60: [CandleInterval.CANDLE_INTERVAL_HOUR, 2400],
                     120: [CandleInterval.CANDLE_INTERVAL_2_HOUR, 2400], 240: [CandleInterval.CANDLE_INTERVAL_4_HOUR, 700],
                     'D': [CandleInterval.CANDLE_INTERVAL_DAY, 2400], 'W': [CandleInterval.CANDLE_INTERVAL_WEEK, 300],
                     'M': [CandleInterval.CANDLE_INTERVAL_MONTH, 120]}

            if isinstance(interval, int):
                val_interval, limit, num_interval = match[interval][0], match[interval][1], interval
            elif interval == 'D':
                val_interval, limit, num_interval = match[interval][0], match[interval][1], 1440
            elif interval == 'W':
                val_interval, limit, num_interval = match[interval][0], match[interval][1], 10080
            else:
                val_interval, limit, num_interval = match[interval][0], match[interval][1], 0

            num_candles = (to_ - from_) // (num_interval * 60 * 1000) if num_interval else limit

            flag = False
            pages = 0
            from__ = from_
            to__ = to_
            if purpose == 'single':
                if num_candles > 720:
                    from__ = to_ - 720 * num_interval * 60 * 1000
                    flag = True
                pages = 1
            elif purpose == 'multiple':
                pages = ceil(num_candles / limit) if num_interval > 0 else 1

            all_candles = []
            with Client(token=self.token, target=self.target) as client:
                for page in range(pages):
                    if purpose == 'multiple':
                        from__ = from_ + (page * num_interval * 60 * 1000 * limit),
                        to__ = from_ + ((page + 1) * num_interval * 60 * 1000 * limit),
                    # print([datetime.fromtimestamp(from__ / 1000, tz=timezone.utc), datetime.fromtimestamp(to__ / 1000, tz=timezone.utc)], val_interval)
                    response = client.market_data.get_candles(
                        instrument_id=uid,
                        interval=val_interval,
                        from_=datetime.fromtimestamp(from__ / 1000, tz=timezone.utc),
                        to=datetime.fromtimestamp(to__ / 1000, tz=timezone.utc),
                        candle_source_type=CandleSource.CANDLE_SOURCE_EXCHANGE).candles
                all_candles.extend(response)
            df = DataFrame(all_candles, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            df = df.rename(columns={'time': 'timestamp'})
            df['timestamp'] = (df['timestamp'].astype('int64') // 10**6).astype(str)

            cols = ['open', 'high', 'low', 'close']
            df[cols] = df[cols].apply(lambda col: col.map(lambda x: x['units'] + x['nano'] / 1e9))
            # print(df)
            return [flag, df, num_candles] if flag else [flag, df]
        except Exception as e:
            print(e)

    def get_orders(self, account_id: str):
        with Client(token=self.token, target=self.target) as client:
            response = client.orders.get_orders(account_id=account_id)
        return response

    def get_order_state(self, account_id: str, order_id: str):
        with Client(token=self.token, target=self.target) as client:
            response = client.orders.get_order_state(account_id=account_id, order_id=order_id)
        return response

    def get_portfolio(self, account_id: str):
        with Client(token=self.token, target=self.target) as client:
            response = client.operations.get_portfolio(account_id=account_id)
        return response

    def get_all_portfolio(self):
        accounts = self.get_accounts_ids()
        for acc in accounts:
            print([acc])
            d = self.get_portfolio(acc)
            data = {'total': float(money_to_decimal(d.total_amount_portfolio).normalize()),
                    'total_s': float(money_to_decimal(d.total_amount_shares).normalize()), 'sh': []}
            for sh in d.positions:
                ticker = self.get_instrument_by_id('uid', sh.instrument_uid).instrument.ticker

                s = {'ticker': ticker, 'lots': float(quotation_to_decimal(sh.quantity_lots).normalize()),
                     'price': float(money_to_decimal(sh.current_price).normalize()),
                     'quantity': float(quotation_to_decimal(sh.quantity).normalize()),
                     'avg': float(money_to_decimal(sh.average_position_price).normalize()),
                     'block': float(quotation_to_decimal(sh.blocked_lots).normalize())}
                data['sh'].append(s)
            accounts[acc]['data'] = data
        return accounts

    def get_average_position_price(self, account_id: str, instrument_uid: str):
        positions = self.get_portfolio(account_id).positions
        for position in positions:
            if position.instrument_uid == instrument_uid:
                return float(money_to_decimal(position.average_position_price).normalize())

    def get_position_info(self, account_id: str, instrument_uid: str):
        port = self.get_portfolio(account_id)
        money = float(money_to_decimal(port.total_amount_currencies).normalize())
        for position in port.positions:
            if position.instrument_uid == instrument_uid:
                return [float(quotation_to_decimal(position.quantity).normalize()), money]
        return [None, money]

    def get_last_price(self, uid: str):
        with Client(token=self.token, target=self.target) as client:
            response = client.market_data.get_last_prices(instrument_id=[uid]).last_prices[0].price
            # response = client.market_data.get_last_prices(instrument_id=[uid])
        return response

    def get_lots(self, uid: str):
        response = self.shares.get_share_by_id('uid', uid).instrument
        return response.lot

    def get_price_l(self, uid: str):
        return [float(quotation_to_decimal(self.get_last_price(uid)).normalize()), self.get_lots(uid)]

    def get_top_ticker_info(self, uid: str, asset_uid: str):
        data = {'price': float(quotation_to_decimal(self.get_last_price(uid)).normalize())}
        fundamental = self.assets.get_asset_data(asset_uid)
        data['high'] = fundamental.high_price_last_52_weeks
        data['low'] = fundamental.low_price_last_52_weeks
        data['avg'] = fundamental.average_daily_volume_last_10_days
        data['cap'] = fundamental.market_capitalization
        return data

    def get_instrument_by_id(self, id_type: str, id_: str, class_code: str = ''):
        id_type = InstrumentIdType.INSTRUMENT_ID_TYPE_POSITION_UID if id_type == 'p_uid' else (
            InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER if id_type == 'ticker' else
            InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI if id_type == 'figi' else
            InstrumentIdType.INSTRUMENT_ID_TYPE_UID if id_type == 'uid' else
            InstrumentIdType.INSTRUMENT_ID_UNSPECIFIED)

        with Client(token=self.token, target=self.target) as client:
            response = client.instruments.get_instrument_by(id_type=id_type, id=id_, class_code=class_code)
            return response

    def post_order(self, instrument_id: str = '', quantity: int = 0, direction: str = '',
                   order_type: str = '', price: Decimal = None, account_id: str = '', sand: bool = None):
        """instrument_id - Instrument identifier, quantity - The number of lots,
           direction - Order direction (buy or sell), order_type - Type of order (market or limit),
           price - Order price, account_id - Account identifier"""
        try:
            direction = OrderDirection.ORDER_DIRECTION_BUY if direction == 'buy' else (
                OrderDirection.ORDER_DIRECTION_SELL if direction == 'sell' else
                OrderDirection.ORDER_DIRECTION_UNSPECIFIED)
            order_type = OrderType.ORDER_TYPE_LIMIT if order_type == 'limit' else (
                OrderType.ORDER_TYPE_MARKET if order_type == 'market' else
                OrderType.ORDER_TYPE_UNSPECIFIED)
            print([price])
            price = decimal_to_quotation(price) if price is not None else decimal_to_quotation(Decimal('1.0'))
            print([price])
            if sand is None:
                target = self.target
            else:
                if sand:
                    target = INVEST_GRPC_API_SANDBOX
                else:
                    target = INVEST_GRPC_API
            print(target)
            print([quantity])
            print([account_id])

            with Client(token=self.token, target=target) as client:
                response = client.orders.post_order(
                    instrument_id=instrument_id,
                    quantity=quantity,
                    direction=direction,
                    order_type=order_type,
                    account_id=account_id,
                    price=price)
            return [response.order_id, response.execution_report_status,
                    [float(money_to_decimal(response.initial_security_price).normalize()), response.direction, response.order_type]]
        except Exception as e:
            print('Tinkoff, post_order', e)

    def cancel_order(self, account_id: str, order_id: str):
        with Client(token=self.token, target=self.target) as client:
            response = client.orders.cancel_order(account_id=account_id, order_id=order_id)
            return response

    @staticmethod
    def is_order_fill(status):
        if status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL:
            return True
        return False

    def get_order_price(self, account_id: str, instrument_id: str, direction, quantity: int, price):
        with Client(token=self.token, target=self.target) as client:
            response = client.orders.get_order_price(
                request=GetOrderPriceRequest(
                    account_id=account_id,
                    instrument_id=instrument_id,
                    direction=direction,
                    quantity=quantity,
                    price=price))
            return response

    def get_candle_stream(self):
        return partial(self.CandleStream, outer=self.info)

    class CandleStream(QObject):
        newCandle = pyqtSignal(list)
        doStop = pyqtSignal()
        finWork = pyqtSignal()

        def __init__(self, outer: list, instrument: str, interval: Literal[1, 3, 5, 15, 30, 60, 120, 240, 'D', 'W', 'M']):
            super().__init__()

            self.token = outer[0]
            self.target = outer[1]
            self.doStop.connect(self.stop)

            self.instrument = instrument
            self.interval = self.calc_interval(interval)

            self.stream = None
            self.running = True

        @pyqtSlot()
        def start_work(self):
            def candle_handler(message):
                if message.candle is not None:
                    candle = message.candle
                    data = [str(int(candle.time.timestamp() * 1000)), float(quotation_to_decimal(candle.open).normalize()),
                            float(quotation_to_decimal(candle.high).normalize()), float(quotation_to_decimal(candle.low).normalize()),
                            float(quotation_to_decimal(candle.close).normalize()), candle.volume]
                    # print(data)
                    self.newCandle.emit(data)

            while self.running:
                try:
                    with Client(token=self.token, target=self.target) as client:
                        market_data_stream = client.create_market_data_stream()
                        self.stream = market_data_stream
                        market_data_stream.subscribe(market_data_request=MarketDataRequest(
                            subscribe_candles_request=SubscribeCandlesRequest(
                                subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                                instruments=[CandleInstrument(instrument_id=self.instrument, interval=self.interval)],
                                waiting_close=True, candle_source_type=CandleSource.CANDLE_SOURCE_EXCHANGE)))
                        for response in market_data_stream:
                            if self.running:
                                candle_handler(response)
                except Exception as e:
                    print('Tinkoff, CandleStream, start_work ', e)
            self.finWork.emit()

        @staticmethod
        def calc_interval(interval: Literal[1, 3, 5, 15, 30, 60, 120, 240, 'D', 'W', 'M']):
            match = {1: SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE, 3: SubscriptionInterval.SUBSCRIPTION_INTERVAL_3_MIN,
                     5: SubscriptionInterval.SUBSCRIPTION_INTERVAL_FIVE_MINUTES, 15: SubscriptionInterval.SUBSCRIPTION_INTERVAL_FIFTEEN_MINUTES,
                     30: SubscriptionInterval.SUBSCRIPTION_INTERVAL_30_MIN, 60: SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_HOUR,
                     120: SubscriptionInterval.SUBSCRIPTION_INTERVAL_2_HOUR, 240: SubscriptionInterval.SUBSCRIPTION_INTERVAL_4_HOUR,
                     'D': SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_DAY, 'W': SubscriptionInterval.SUBSCRIPTION_INTERVAL_WEEK,
                     'M': SubscriptionInterval.SUBSCRIPTION_INTERVAL_MONTH}
            return match[interval]

        def stop(self):
            try:
                self.running = False
                self.stream.stop()
            except Exception as e:
                print('Tinkoff, CandleStream, stop ', e)

    def get_order_state_stream(self):
        return partial(self.OrderStateStream, outer=self.info, account_method=self.get_accounts, order_state_method=self.get_order_state)

    class OrderStateStream(QObject):
        sendState = pyqtSignal(object)
        doStop = pyqtSignal()
        finWork = pyqtSignal()

        def __init__(self, outer: list, account_method: Callable, order_state_method: Callable, order_id: str, wait_time: int):
            super().__init__()
            self.token = outer[0]
            self.target = outer[1]

            self.accounts = [acc.id for acc in account_method()]
            self.get_order_state = order_state_method
            self.order_id = order_id
            self.wait_time = wait_time

            self.stream = None
            self.running = True

            self.doStop.connect(self.stop)
            self.work_flag = True
            print(1)

        @pyqtSlot()
        def start_work(self):
            while True:
                try:
                    with Client(token=self.token, target=self.target) as client:
                        order_stream = client.orders_stream.order_state_stream(
                            request=OrderStateStreamRequest(accounts=self.accounts, ping_delay_ms=2000))
                        start = datetime.now()
                        is_checked = False
                        for status in order_stream:
                            print('пинг цикла ожидание изменения состояния ордера')
                            if not is_checked:
                                for acc in self.accounts:
                                    state = self.get_order_state(acc, self.order_id)
                                if state is not OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_NEW:
                                    print(state.executed_order_price, 99999)
                                    if state.execution_report_status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL:
                                        # self.sendState.emit(float(money_to_decimal(state.executed_order_price).normalize()))
                                        self.sendState.emit(['fill', [float(money_to_decimal(state.executed_order_price).normalize()),
                                                                      state.execution_report_status, state.direction, state.order_type]])
                                        is_checked = True
                                        break
                                    elif state.execution_report_status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_CANCELLED:
                                        # self.sendState.emit('canceled')
                                        self.sendState.emit(['canceled', [float(money_to_decimal(state.initial_order_price).normalize()),
                                                                          state.execution_report_status, state.direction, state.order_type]])
                                        is_checked = True
                                        break
                                is_checked = True

                            if not self.work_flag:
                                break
                            end = datetime.now()
                            if 0 < self.wait_time <= (end - start).total_seconds():
                                self.sendState.emit(['expired', [float(money_to_decimal(state.initial_order_price).normalize()),
                                                                 state.execution_report_status, state.direction, state.order_type]])
                                break
                            else:
                                state = status.order_state
                                if state is not None:
                                    print('у какого-то заказа изменилось')
                                    if state.order_id == self.order_id:
                                        if state.execution_report_status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL:
                                            # self.sendState.emit(float(money_to_decimal(state.executed_order_price).normalize()))
                                            self.sendState.emit(['fill', [float(money_to_decimal(state.executed_order_price).normalize()),
                                                                          state.execution_report_status, state.direction, state.order_type]])
                                            break
                                        elif state.execution_report_status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_CANCELLED:
                                            # self.sendState.emit('canceled')
                                            self.sendState.emit(['canceled', [float(money_to_decimal(state.initial_order_price).normalize()),
                                                                              state.execution_report_status, state.direction, state.order_type]])
                                            break
                        order_stream = None
                        print('стрим состояния заказа кончился')

                        break

                except Exception as e:
                    print('Tinkoff, OrderStateStream, start_work ', e)
                    print('перезапуск Tinkoff, OrderStateStream, start_work')
            print('стрим состояния заказа кончился')
            self.finWork.emit()

        def stop(self):
            self.work_flag = False

    class Assets:
        def __init__(self, outer):
            self.outer = outer

        def get_assets(self):
            with Client(token=self.outer.token, target=self.outer.target) as client:
                response = client.instruments.get_assets(
                    AssetsRequest(instrument_type=InstrumentType.INSTRUMENT_TYPE_SHARE,
                                  instrument_status=InstrumentStatus.INSTRUMENT_STATUS_ALL)).assets
                return response

        def get_asset_uid_by_instrument_uid(self, uid: str):
            return next(a for a in self.get_assets() if any(i.uid == uid for i in a.instruments)).uid

        def get_asset_data(self, asset_uid: str):
            with Client(token=self.outer.token, target=INVEST_GRPC_API) as client:
                response = client.instruments.get_asset_fundamentals(
                    GetAssetFundamentalsRequest([asset_uid])).fundamentals[0]
            return response

    class SandBox:
        def __init__(self, outer):
            self.outer = outer

        def sand_add_account(self, name: str):
            with Client(token=self.outer.token, target=INVEST_GRPC_API_SANDBOX) as client:
                response = client.sandbox.open_sandbox_account(name=name)
                return response

        def sand_close_account(self, account_id: str):
            with Client(token=self.outer.token, target=INVEST_GRPC_API_SANDBOX) as client:
                response = client.sandbox.close_sandbox_account(account_id=account_id)
                return response

        def sand_pay(self, account_id: str, amount: Decimal):
            amount = decimal_to_quotation(amount)
            amount = MoneyValue(currency='rub', units=amount.units, nano=amount.nano)
            with Client(token=self.outer.token, target=INVEST_GRPC_API_SANDBOX) as client:
                response = client.sandbox.sandbox_pay_in(account_id=account_id, amount=amount)
                return response

    class Shares:
        def __init__(self, outer):
            self.outer = outer

        def get_shares(self):
            with Client(token=self.outer.token, target=self.outer.target) as client:
                return client.instruments.shares().instruments

        def get_share_ids(self, ticker: str):
            for share in self.get_shares():
                if share.ticker == ticker:
                    asset_uid = self.outer.assets.get_asset_uid_by_instrument_uid(share.uid)
                    return {'ticker': share.ticker, 'class_code': share.class_code, 'figi': share.figi, 'uid': share.uid,
                            'p_uid': share.position_uid, 'asset_uid': asset_uid, 'name': share.name}

        def get_share_by_id(self, id_type: str, id_: str, class_code: str = ''):
            id_type = InstrumentIdType.INSTRUMENT_ID_TYPE_POSITION_UID if id_type == 'p_uid' else (
                InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER if id_type == 'ticker' else
                InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI if id_type == 'figi' else
                InstrumentIdType.INSTRUMENT_ID_TYPE_UID if id_type == 'uid' else
                InstrumentIdType.INSTRUMENT_ID_UNSPECIFIED)

            with Client(token=self.outer.token, target=self.outer.target) as client:
                response = client.instruments.share_by(id_type=id_type, id=id_, class_code=class_code)
                return response

# Пример использования
def main():
    token = "t.UpziRwYzxPSr9xk30CoYcpOCc0WVQXLdhbzAJ2S6-zCd3U6wliu4nQDszTjg8FsqU_fXoNu9AosaWfpjP4cLlA"
    tinkoff = Tinkoff(token)
    # with Client(token=token, target=INVEST_GRPC_API_SANDBOX) as client:
    #     client.cancel_all_orders(account_id=AccountId('3517a708-e31e-42bc-b1bf-a6fdee1ffcf4'))

    # for share in tinkoff.get_shares():
    #     if share.ticker == 'FLOT':
    #         print(share)
    # print(tinkoff.get_shares())

    # # Получение списка счетов
    # accounts = tinkoff.get_accounts()
    # print("Счета:", accounts)
    #
    # orders = tinkoff.get_orders('2207282340')
    # print(orders)
    #
    # a = tinkoff.sand_add_account('2')
    # print(a)

    # b = tinkoff.sand_get_accounts()
    # print(b)

    # c = tinkoff.sand_close_account('75891790-eaf8-4f3b-8620-cac9b8c0c64f')
    # print(c)

    # d = tinkoff.sandbox.sand_pay('3517a708-e31e-42bc-b1bf-a6fdee1ffcf4', Decimal(10000))
    # print(d)



    # p = tinkoff.get_portfolio('3517a708-e31e-42bc-b1bf-a6fdee1ffcf4')
    # print(p)

    # s = tinkoff.get_share_ids('FLOT')
    # print(s)
    # ['BBG000R04X57', 'FLOT', 'TQBR', 'RU000A0JXNU8', '21423d2d-9009-4d37-9325-883b368d13ae', '4419d6f3-b412-421e-8745-3bc6b7a93b09']
    # s = tinkoff.get_share_by_id('p_uid', '4419d6f3-b412-421e-8745-3bc6b7a93b09')
    # print(s)

    # a = tinkoff.get_top_ticker_info('e6123145-9665-43e0-8413-cd61b8aa9b13', '40d89385-a03a-4659-bf4e-d3ecba011782')
    # .get_last_price('21423d2d-9009-4d37-9325-883b368d13ae')
    # locale = QLocale(QLocale.Language.Russian).toString(a['cap'], 'f', len(str(a['cap']).split('.')[1]))
    # print({i: QLocale(QLocale.Language.Russian).toString(a[i], 'f', len(str(a[i]).split('.')[1])) for i in a})
    # print(a)
    # print(CandleInterval())

    # o = tinkoff.get_last_price('e6123145-9665-43e0-8413-cd61b8aa9b13')
    # print(o)

    # a = tinkoff.get_candle('e6123145-9665-43e0-8413-cd61b8aa9b13', 1, 1746034827956, 1746040827957, 'single')
    # print(a)
    # a = tinkoff.get_portfolio('3517a708-e31e-42bc-b1bf-a6fdee1ffcf4')
    # print(a)

    # a = tinkoff.post_order(instrument_id='e6123145-9665-43e0-8413-cd61b8aa9b13', quantity=1, direction='buy', order_type='limit', price=Decimal(200),
    #                        account_id='3517a708-e31e-42bc-b1bf-a6fdee1ffcf4', sand=True)
    # print(a)
    # a = tinkoff.cancel_order('3517a708-e31e-42bc-b1bf-a6fdee1ffcf4', 'c1e93d1a-7436-4632-bd55-f6419ec0455d')
    # print(a)
    a = tinkoff.get_orders('3517a708-e31e-42bc-b1bf-a6fdee1ffcf4')
    print(a)
    # a = tinkoff.get_order_price('3517a708-e31e-42bc-b1bf-a6fdee1ffcf4', 'e6123145-9665-43e0-8413-cd61b8aa9b13', OrderDirection.ORDER_DIRECTION_BUY, 2, decimal_to_quotation(Decimal('306.42')))
    # print(a)

    # a = tinkoff.get_order_state_stream()
    # a(order_id='8a946f0f-b577-40b2-88f4-974f51740bd6')

    # a = tinkoff.get_all_portfolio()
    # for i in a:
    #     print([i])
    # print([a])

    # if accounts:
    #     account_id = accounts[0].id  # Берем первый счет
    #     portfolio = tinkoff.get_portfolio(account_id=account_id)
    #     print("Портфель:", portfolio)
    #
    #     figi = "FIGI_EXAMPLE"  # Пример figi для стакана
    #     orderbook = tinkoff.get_orderbook(figi)
    #     print("Стакан заявок:", orderbook)


if __name__ == "__main__":
    main()
