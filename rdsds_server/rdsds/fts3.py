#!/usr/bin/python

from transfer import Transfer
import commands
import os
import logging
import StringIO
import time
from db_manage import crud
import tempfile
# Log setting and generate a logfile on the current place
logpath = os.getcwd() + "/dsds_server_logs"
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(message)s', filename=logpath)
logger = logging.getLogger('dsds_server_logs')

class FTS(Transfer):

    def __init__(self):
        self.dpid = []
        self.diff_list = []
        self.subscriber_email = []
        self.fts_status_id = []
        self.fts3_host = []
        self.proxy_path = []
        self.filetransfer = []

    def create_transferlist(self, dpid, diff_list):

        file_path = crud('', dpid, "file_location", '')
        filetransfer = []
        for row in file_path:
            hostname = row[2]
        subscriptions = crud('', '', "get_subs", '')
        for row in subscriptions:
            subscriber_dataset = row[1]
            if subscriber_dataset == dpid:
                subs_hostname_list = crud('', dpid, "get_subs_host", '')
                for host in subs_hostname_list:
                    destination_list = host[0]
                    folder_path = host[1]

                    for n in diff_list:
                        filetransfer.append("gsiftp://" + hostname + n + " gsiftp://" + destination_list + folder_path[:-1] + n + '\n')
        return filetransfer

    def delegate(self, fts3_host, proxy_path):
        """ FTS fts-delegation-init"""
        verbose_mode = "-v -s"
        verbose_mode1 = "--proxy"
        fts3_delegation_cmd = """ fts-delegation-init %s %s %s %s""" % (verbose_mode, fts3_host, verbose_mode1, proxy_path)
        fts3_delegation_output = commands.getstatusoutput(fts3_delegation_cmd)

        if "problem" in fts3_delegation_output[1]:
            logging.error('[ERROR] Something wrong on FTS delegation')
            logging.error(fts3_delegation_output[1])
            return False
        elif "expired" in fts3_delegation_output[1]:
            logging.error('[ERROR] Something wrong on FTS delegation')
            logging.error(fts3_delegation_output[1])
            return False
        else:
            return True

    def submit(self, fts3_host, proxy_path, filetransfer):
        """ FTS fts-transfer-submit"""
        try:
            fts3_temp_file = tempfile.NamedTemporaryFile()
            logging.info('fts3_temp: %s', fts3_temp_file)
            logging.info('fts3_temp_name: %s', fts3_temp_file.name)
            fts3_temp_file.writelines(filetransfer)
            fts3_temp_file.seek(0)
            transfer_list = fts3_temp_file.name
            try:
                verbose_mode1 = '-o -m --retry 0 -s'
                verbose_mode2 = '--proxy'
                verbose_mode3 = '-f'
                fts3_transfer_submit_cmd = """ fts-transfer-submit %s %s %s %s %s %s""" % (
                verbose_mode1, fts3_host, verbose_mode2, proxy_path, verbose_mode3, transfer_list)
                print fts3_transfer_submit_cmd
                fts3_transfer_submit_output = commands.getstatusoutput(fts3_transfer_submit_cmd)
                print fts3_transfer_submit_output
                fts_status_id = fts3_transfer_submit_output[1]
                return fts_status_id
            except TypeError:
                return False
        finally:
            logging.info('Remove this file: transfer_list')
            endtime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
            logging.info('transfer end time %s', endtime)
            fts3_temp_file.close()

    def status(self, fts_status_id, fts3_host, proxy_path):

        """ fts-transfer-status """
        query_num = 10
        while query_num > 0:
            logging.info('Query time is %s', query_num)
            verbose_mode1 = '-s'
            verbose_mode2 = '--proxy'
            verbose_mode3 = '-d -l'
            filter_cmd = '| grep State:'
            filter_cmd_2 = '| grep Reason:'

            fts3_transfer_status_cmd = """ fts-transfer-status %s %s %s %s %s %s %s""" % (
            verbose_mode1, fts3_host, verbose_mode2, proxy_path, verbose_mode3, fts_status_id, filter_cmd)

            fts3_transfer_total_status_cmd = """ fts-transfer-status %s %s %s %s %s %s %s""" % (
            verbose_mode1, fts3_host, verbose_mode2, proxy_path, verbose_mode3, fts_status_id, filter_cmd_2)

            fts3_transfer_status_output = commands.getstatusoutput(fts3_transfer_status_cmd)
            fts_status_lines = StringIO.StringIO(fts3_transfer_status_output)
            lines = fts_status_lines.readlines()
            logging.info('FTS3 Transfer Status is %s', lines[0])

            fts3_transfer_total_status_output = commands.getstatusoutput(fts3_transfer_total_status_cmd)
            fts_total_status_lines = StringIO.StringIO(fts3_transfer_total_status_output)
            reason = fts_total_status_lines.readlines()
            logging.info('FTS3 Transfer Status Reason is %s', reason[0])
            query_num -= 1
            time.sleep(5)

        return {'query_status': lines[0], 'query_info': reason[0]}

    def cancel(self, fts_status_id, fts3_host, proxy_path):

        try:
            verbose_mode = '-v -s'
            verbose_mode1 = '--proxy'
            filter_cmd = '| grep'
            fts3_transfer_cancel_cmd = """ fts-transfer-cancel %s %s %s %s %s %s %s""" % (
            verbose_mode, fts3_host, verbose_mode1, proxy_path, fts_status_id, filter_cmd, fts_status_id)
            fts3_transfer_cancel_output = commands.getstatusoutput(fts3_transfer_cancel_cmd)
            return fts3_transfer_cancel_output
        except TypeError:
            return False
