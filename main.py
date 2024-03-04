import sqlite3
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from tabulate import tabulate


def database_init(cursor):
    cursor.executescript('''
        drop table if exists cryptocurrency;
        create table cryptocurrency
        (
            id         integer primary key,
            rank       integer,
            name       text,
            symbol     text,
            price      real,
            market_cap real
        );
    ''')
    cursor.connection.commit()


def database_insert(cursor, cmc_id: int, rank: int, name: str, symbol: str, price: float, market_cap: float):
    cursor.execute('''
        insert into cryptocurrency (id, rank, name, symbol, price, market_cap)
        values (?, ?, ?, ?, ?, ?);
        ''', (cmc_id, rank, name, symbol, price, market_cap))
    cursor.connection.commit()


def database_get_columns_names(cursor):
    return [description[0] for description in cursor.description]


def database_get(cursor, cryptocurrency_symbol: str):
    cursor.execute('''
        select name, symbol, price, market_cap
        from cryptocurrency
        where symbol like ?;
        ''', ('%' + cryptocurrency_symbol + '%',))
    return cursor.fetchall()


def table_print(data: list, header: list):
    print('\n', tabulate(data, headers=header), '\n')


def fetch_data(cursor):
    # Free plan is designed for up to 1 free call every 5 seconds
    url = 'https://sandbox-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

    # WARNING! VARIABLE CONTAINS API KEY
    api_key = 'b54bcf4d-1bca-4e8e-9a24-22ff2c3d462c'

    # Up to 5000 records per request
    entries_number = 100

    # Currency for providing data on cryptocurrency quotes
    currency = 'USD'

    parameters = {
        'start': '1',
        'limit': entries_number,
        'convert': currency
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters, headers=headers)

        if response.status_code != 200:
            exit(response)

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        exit(e)

    raw_data = json.loads(response.text)
    # print(raw_data)

    for data in raw_data['data']:
        database_insert(cursor, int(data['id']), int(data['cmc_rank']), data['name'], data['symbol'],
                        float(data['quote']['USD']['price']),
                        float(data['quote']['USD']['market_cap']))


def main():
    database = sqlite3.connect('quotes.sqlite')
    cursor = database.cursor()

    database_init(cursor)
    fetch_data(cursor)

    while True:
        input_str = str(input(
            "Для выхода из программы нажмите [Q], для вывода всех значений введите [A], а для поиска введите символ: "))
        if input_str == "Q" or input_str == "q":
            break
        elif input_str == "A" or input_str == "a":
            data = database_get(cursor, '')
        else:
            data = database_get(cursor, input_str)

        columns_names = database_get_columns_names(cursor)
        table_print(data, columns_names)

    database.close()


if __name__ == '__main__':
    main()
