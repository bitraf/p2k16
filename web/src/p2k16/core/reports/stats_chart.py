import numpy as np
import pandas
import pandas as pd
import sqlalchemy.engine.interfaces
from matplotlib.figure import Figure


def query(con: sqlalchemy.engine.interfaces.Connectable):
    sql = '''
SELECT date_trunc('month', p.payment_date)::date      AS date,
       SUM(amount)                                    AS sum,
       COUNT(*)                                       AS count,
       SUM(CASE WHEN amount >= 500 THEN 1 ELSE 0 END) AS count_500_plus,
       SUM(CASE WHEN amount < 500 THEN 1 ELSE 0 END)  AS count_lt_500
FROM stripe_payment p
GROUP BY date_trunc('month', p.payment_date)::date
ORDER BY date;
'''

    df = pd.read_sql_query(sql, con, parse_dates=['date'])
    df.index = df['date']

    return df


def run(df: pandas.DataFrame):
    fig = Figure(figsize=[16, 16])
    (ax, ax2) = fig.subplots(nrows=2, sharey=False)

    title = 'Bitraf membership fees per month'

    dates = df['date']
    sums = df['sum']

    df.plot(y=['sum'], linewidth=3, title=title, ax=ax)
    xtick = pd.date_range(start=df.index.min(), end=df.index.max(), freq='W')
    ax.set_xticks(xtick, minor=True)
    ytick = np.arange(0, sums.max(), 5000)
    ax.set_yticks(ytick, minor=True)
    ax.grid('on', which='minor', axis='x')
    ax.grid('off', which='major', axis='x', linewidth=2)
    ax.grid('on', which='major', axis='y', linewidth=2)
    ax.grid('on', which='minor', axis='y')

    ax = ax2
    title = 'Bitraf active members'

    xtick = pd.date_range(start=df.index.min(), end=df.index.max(), freq='W')
    ytick = np.arange(0, df['count'].max(), 10)
    df.plot(y=['count', 'count_500_plus', 'count_lt_500'],
            linewidth=3,
            title=title,
            ax=ax,
            xticks=xtick,
            yticks=ytick)
    ax.legend(['All members', 'Full members (500kr)', 'Supporting members (300kr)'])
    ax.grid('on', which='minor', axis='x')
    ax.grid('off', which='major', axis='x', linewidth=2)
    ax.grid('on', which='major', axis='y', linewidth=2)
    ax.grid('on', which='minor', axis='y')

    return fig
