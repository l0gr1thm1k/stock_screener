"""
This is a package to access metrics from Morningstar financials
"""

import csv
import json
import numpy as np
import pandas as pd
import re
import urllib.request

from bs4 import BeautifulSoup
from datetime import date


class KeyRatiosDownloader(object):

    def __init__(self, table_prefix="morningstar_"):
        self._table_prefix = table_prefix

    def download(self, ticker, conn=None, region='GBR', culture='en_US', currency='USD'):
        url = (r'http://financials.morningstar.com/ajax/exportKR2CSV.html?' +
               r'&callback=?&t={t}&region={reg}&culture={cult}&cur={cur}'.format(t=ticker,
                                                                                 reg=region,
                                                                                 cult=culture,
                                                                                 cur=currency))
        with urllib.request.urlopen(url) as response:
            tables = self._parse_tables(response)
            response_structure = [
                (u'Financials', u'Key Financials'),
                (u'Key Ratios -> Profitability', u'Key Margins % of Sales'),
                (u'Key Ratios -> Profitability', u'Key Profitability'),
                (u'Key Ratios -> Growth', None),
                (u'Revenue %', u'Key Revenue %'),
                (u'Operating Income %', u'Key Operating Income %'),
                (u'Net Income %', u'Key Net Income %'),
                (u'EPS %', u'Key EPS %'),
                (u'Key Ratios -> Cash Flow', u'Key Cash Flow Ratios'),
                (u'Key Ratios -> Financial Health', u'Key Balance Sheet Items (in %)'),
                (u'Key Ratios -> Financial Health', u'Key Liquidity/Financial Health'),
                (u'Key Ratios -> Efficiency Ratios', u'Key Efficiency Ratios')]
            frames = self._parse_frames(tables, response_structure)

            #############################
            # ERROR HANDLING FOR RATIOS #
            #############################

            if len(ticker) == 0:
                raise ValueError("You did not enter a ticker symbol. Please try again.")
            elif frames == "MorningStar could not find the ticker":
                raise ValueError("MorningStar couldn't find the ticker you entered or it's Invalid. Please try again.")
            currency = re.match(u'^.* ([A-Z]+) Mil$', frames[0].index[0]).group(1)
            frames[0].index.name += u' ' + currency
            if conn:
                self._upload_frames_to_db(ticker, frames, conn)
            return frames

    @staticmethod
    def _parse_tables(response):
        num_commas = 5
        pat_commas = r'(.*,){%d,}' % num_commas
        tables = []
        table_name = None
        table_rows = None
        for line in response:
            line = line.decode(u'utf-8').strip()
            match = re.match(pat_commas, line)
            if match:
                for row in csv.reader([line]):
                    table_rows.append(row)
            else:
                if table_name and table_rows:
                    tables.append([table_name, pd.DataFrame(table_rows)])
                if line != u'':
                    table_name = line
                table_rows = []
        if table_name and table_rows:
            tables.append([table_name, pd.DataFrame(table_rows)])
        return tables

    @staticmethod
    def _parse_frames(tables, response_structure):
        if len(tables) == 0:
            return "MorningStar could not find the ticker"
        period_start = tables[0][1].ix[0][1]
        period_month = pd.datetime.strptime(period_start, u'%Y-%m').month
        period_freq = pd.tseries.offsets.YearEnd(month=period_month)
        frames = []
        for index, (check_name, frame_name) in enumerate(response_structure):
            if frame_name and tables[index][0] == check_name:
                frame = KeyRatiosDownloader._process_frame(tables[index][1], frame_name, period_start, period_freq)
                if frame is not None and frame.index.size > 0:
                    frames.append(frame)
        return frames

    @staticmethod
    def _process_frame(frame, frame_name, period_start, period_freq):
        output_frame = frame.set_index(frame[0])
        del output_frame[0]
        output_frame.index.name = frame_name
        output_frame.columns = pd.period_range(period_start, periods=len(output_frame.ix[0]), freq=period_freq)
        output_frame.columns.name = u'Period'

        if re.match(r'^\d{4}-\d{2}$', output_frame.ix[0][0]):
            output_frame.drop(output_frame.index[0], inplace=True)
        output_frame.replace(u',', u'', regex=True, inplace=True)
        output_frame.replace(u'^\s*$', u'NaN', regex=True, inplace=True)
        return output_frame.astype(float)

    def _upload_frames_to_db(self, ticker, frames, conn):
        for frame in frames:
            table_name = self._get_db_table_name(frame)
            if not _db_table_exists(table_name, conn):
                _db_execute(self._get_db_create_table(frame), conn)
            _db_execute(self._get_db_replace_values(ticker, frame), conn)

    @staticmethod
    def _get_db_name(name):
        name = (name.lower()
                .replace(u'/', u' per ')
                .repalce(u'&', u' and ')
                .replace(u'%', u' percent '))
        name = re.sub(r'[^a-z0-9]', u' ', name)
        name = re.sub(r'\s+', u' ', name).strip()
        return name.replace(u' ', u'_')

    def _get_db_table_name(self, frame):
        return self._table_prefix + self._get_db_name(frame.index.name)

    def _get_db_create_table(self, frame):
        columns = u',\n'.join([u' `%s` DECIMAL(20,5) DEFAULT NULL COMMENT "%s"' %
                               (self._get_db_name(name), name) for name in frame.index.values])
        table_name = self._get_db_table_name(frame)
        return (
            u'CREATE TABLE `%s` (\n' % table_name +
            u' `ticker` VARCHAR(50) NOT NULL COMMENT "Exchange:Ticker",\n' +
            u' `period` DATE NOT NULL COMMENT "Period",\n' +
            u'%s,\n' % columns +
            u' PRIMARY KEY USING BTREE (`ticker`, `period`),\n' +
            u' KEY `ix_ticker` USING BTREE (`ticker))\n' +
            u'ENGINE=MyISAM DEFAULT CHARSET=utf8\n' +
            u'COMMENT = "%s"' % frame.index.name)

    def _get_db_replace_values(self, ticker, frame):
        columns = ([u'`ticker`', u'`period`'] +
                   [u'`%s`' % self._get_db_name(name) for name in frame.index.values])
        return (u'REPLACE INTO `%s`\n' % self._get_db_table_name(frame) +
                u' (%s)\nVALUES\n' % u',\n '.join(columns) +
                u',\n'.join([u'("' + ticker + u'", "' + column.strftime(u'%Y-%m-%d') +
                             u'", ' +
                             u', '.join([u'NULL' if np.isnan(x) else u'%.5f' % x for x in frame[column].values]) +
                             u')' for column in frame.columns]))


class FinancialsDownloader(object):

    def __init__(self, table_prefix=u'morningstar_'):
        self._table_prefix = table_prefix

    def download(self, ticker, conn=None):
        result = {}
        if len(ticker) == 0:
            raise ValueError(u"You did not enter a ticker symbol. Please try again.")
        for report_type, table_name in [(u'is', u'income_statement'),
                                        (u'bs', u'balance_sheet'),
                                        (u'cf', u'cash_flow')]:
            frame = self._download(ticker, report_type)
            result[table_name] = frame
            if conn:
                self._upload_frame(frame, ticker, self._table_prefix + table_name, conn)
        if conn:
            self._upload_unit(ticker, self._table_prefix + u'init', conn)
        result[u'period_range'] = self._period_range
        result[u'fiscal_year_end'] = self._fiscal_year_end
        result[u'currency'] = self._currency
        return result

    def _download(self, ticker, report_type):
        url = (r'http://financials.morningstar.com/ajax/' +
               r'ReportProcess4HtmlAjax.html?&t=' + ticker +
               r'&region=usa&culture=en-US&cur=USD' +
               r'&reportType=' + report_type + r'&period=12' +
               r'&dataType=A&order=asc&columnYear=5&rounding=3&view=raw')
        with urllib.request.urlopen(url) as response:
            json_text = response.read().decode(u'utf-8')
            if len(json_text) == 0:
                raise ValueError("MorningStar cannot find the ticker symbol you entered or it is INVALID. "
                                 "Please try again.")
            json_data = json.loads(json_text)
            result_soup = BeautifulSoup(json_data[u'result'], u'html.parser')
            return self._parse(result_soup)

    def _parse(self, soup):
        

def _db_table_exists(table_name, conn):
    cursor = conn.cursor()
    cursor.execute(u"""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name ='{0}'""".format(table_name))
    table_exists = cursor.fetchone()[0] == 1
    cursor.close()
    return table_exists


def _db_execute(query, conn):
    cursor = conn.cursor()
    cursor.execute(query)
    cursor.close()
