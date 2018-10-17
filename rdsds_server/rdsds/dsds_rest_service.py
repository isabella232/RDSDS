#!/usr/bin/python
# REST service module

# local imports
from dsds import app
#import google_oauth
from db_manage import crud
from db_config import config

# standard imports
from flask import Flask, jsonify, request, Blueprint, make_response, abort, Response
import commands
import re
import logging
import StringIO
import json
import time
import difflib
import requests
import os
import warnings
import tempfile
from rdsds_email import EMAIL_METHOD
from fts3 import FTS
email_method = EMAIL_METHOD()
fts_transfer = FTS()


# Log setting and generate a logfile on the current place
logpath = os.getcwd() + "/dsds_server_logs"
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(message)s', filename=logpath)
logger = logging.getLogger('dsds_server_logs')

from functools import wraps
from flask import g, request, redirect, url_for

#Configuration info
suffix = 'xtc|txt|log|dat|gz|file|doc|img|tgz|out|json|[a-zA-Z0-9]{1,100}'
pattern = '(\/[\w\/]+$)'
file_list = []
file_total = 0
fts3_host = 'https://fts3.du2.cesnet.cz:8446'
proxy_path = '/var/www/files/x509up_u1000'


#401 error decorator
@app.errorhandler(401)
def custom_401(error):
    return Response('<user not authorized for this resource...>', 401, {'WWWAuthenticate': 'Basic realm="Login Required"'})


#login decorator function
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = request.headers['token'] # fetch the user authorized token from the client
#            logging.info(token)
#            logging.info("fetched token from decorated @login")
            authorized_user_list = crud(token, '', "get_session", '')
            #checks whether a valid session exists in session table with proposed token
            if authorized_user_list:
                authorized_user = authorized_user_list[0][0]
            else:
                abort(401)
        except NameError:
            logging.error('user not authorized for this resource')
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

# internal functions used by endpoint functions

def delete_files():
    try:
        dpid = request.form['dpid']
        filepath = request.form['filepath']
        file_id = crud('', dpid, "file_id", filepath)
        dataset_last_version = crud('', dpid, "dataset_get_last_version", '')
        dataset_version_int = dataset_last_version[0][0]
        dataset_working_version = dataset_version_int + 1
        if file_id:
            for name in file_id:
                file_id = name[0]
                delete_file = crud(dataset_working_version, dpid, "delete_file", file_id)
            return delete_file
        else:
            logging.warning('[Delete Files] There is no File_id!! This file does not exist!!')
    except:
        logging.warning('[Delete Files] There is no datasetPID or FilePath')


def dataset_status_check(dpid):

# Check dataset status and return the result to the client side let users choose to delete or not
    dataset_status = crud('', dpid, "dataset_status", '')
    for status in dataset_status:
        status_result = status[0]
        return status_result

def list_dataset(dpid, version):

    if version == 'none':
        dataset_last_version = crud('', dpid, "get_dataset_last_version", '')
        dataset_version_int = dataset_last_version[0][0]
        current_working_dataset = dataset_version_int + 1
        serv_message = crud(current_working_dataset, dpid, "list_dataset", '')
    else:
        dataset_version_int = version
        serv_message = crud(dataset_version_int, dpid, "list_dataset", '')
    return serv_message

def verify_file(dpid):

    # Get file information from local DB
    client_response = []
    DBfile_name_dic = sorted(DBfile_check(dpid))

    # Get file information from remote site
    file_exists_dic = sorted(fremotefile_exist_check(dpid))
    # Compare if remote files are the same in local DB
    # Remote Site -> Local DB
    for n in file_exists_dic:
        if n in DBfile_name_dic:
            client_response.append("Filename and Timestamp are matched on Remote Site")
        else:
            message = checksum_check(dpid, n[0])
            client_response.append('[WARNING], ' + n[0] + ' does not exist in remote site or File/Timestamp changes, will continue checking file checksum')
            logging.error(message)
            logging.error(' %s does not exist in remote site or File/Timestamp changes, will continue checking file checksum', n[0])
            client_response.append('\n'+message)

#    # Compare if local DB files are the same in remote site
     # Local DB -> Remote Site
    for m in DBfile_name_dic:
        if m in file_exists_dic:
            client_response.append("Filename and Timestamp are matched on Local DB")
        else:
            message = checksum_check(dpid, m[0])
            client_response.append('[WARNING], ' + m[0] + ' does not exist in local DB or File/Timestamp changes, will continue checking file checksum')
            logging.error(message)
            logging.error(' %s does not exist in local DB or File/Timestamp changes, will continue checking file checksum', m[0])
            client_response.append('\n' + message)
    response = '\n'.join(map(str, client_response))
    return response

def check_proxy_cert():
    ## We cannot use /tmp because http as a system user does not read from /tmp
    if os.path.islink("/var/www/files/proxy.crt"):
        logging.info('/var/www/files/proxy.crt exists and continue checking the details')
        grid_proxy_cmd = """grid-proxy-info -debug -f /var/www/files/x509up_u1000"""
        status, proxy_output = commands.getstatusoutput(grid_proxy_cmd)
        available_time = proxy_output.split()[-1]
        error_message = proxy_output.split()[0]
        if "0:00:00" in available_time:
            logging.warning('Proxy certificate is not available')
            return False
        elif "ERROR" in available_time:
            logging.warning('Proxy certificate is not available')
            return False
        elif "ERROR" in error_message:
            logging.warning('Proxy certificate is not available')
            return False
        else:
            return True
    else:
        logging.warning('Proxy certificate missing. Please check grid-proxy-info')
        return False

def diff(dpid, v1, v2):

    server_message = crud(v1, dpid, "diff_db_version", v2)
    return server_message

def get_subscription():

    subs_list = crud('', '', "get_subs", '')
    return subs_list

def data_transfer(dpid, diff_list, subscriber_email):

    # Create a host_trans_temp with the source hostname and destination hostname
    # Create a gridftp_trans_file_temp with the file names
    # Perform globus-url-copy command line (Gridftp)
    # Remove two files after the transfer is done

    updatetime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
    logging.info('Tansfer time is %s', updatetime)

    file_path = crud('', dpid, "file_location", '')
    filelist = []
    sourcelist = []
    for row in file_path:
        hostname = row[2]

    subscriptions = get_subscription()
    for row in subscriptions:
        subscriber_dataset = row[1]
        if subscriber_dataset == dpid:
            subs_hostname_list = crud('', dpid, "get_subs_host", '')
            for host in subs_hostname_list:
                destination_list = host[0]
                folder_path = host[1]
                sourcelist.append('@source'+'\n'+hostname+'\n'+'@destination'+'\n'+destination_list)

            host_trans_temp = tempfile.NamedTemporaryFile()
            gridftp_trans_file_temp = tempfile.NamedTemporaryFile()

            host_trans_temp.writelines(sourcelist)
            host_trans_temp.seek(0)

            trans_sourceurl = host_trans_temp.name

    # Create a gsiftp_file.txt with the file names
    targetlist = []
    for n in diff_list:

        targetlist.append("gsiftp://" + n + "  gsiftp://" + folder_path + n + n.split("/")[-1] +'\n')

    logging.info('filelist temp %s', gridftp_trans_file_temp)
    logging.info('filelist file name %s :', gridftp_trans_file_temp.name)
    gridftp_trans_file_temp.writelines(targetlist)
    gridftp_trans_file_temp.seek(0)

    trans_destinationurl = gridftp_trans_file_temp.name
    logging.info(trans_destinationurl)

    # Command line sample: time globus-url-copy -rst -p 50 -af hosts.txt -f gsiftp_file.txt

    verbose_mode = "-rst -vb -p 50 -af"
    verbose_1_mode = '-cd -f'
    transfer_cmd = """globus-url-copy %s %s %s %s """ % (verbose_mode, trans_sourceurl, verbose_1_mode, trans_destinationurl)
    status, transfer_output = commands.getstatusoutput(transfer_cmd)

    if "error" in transfer_output:
        logging.error('[ERROR] Something wrong during transfer, please check it')
        logging.error(transfer_output)
        logging.error("[ERROR] File Transfer is failed, please check it!!!")
        email_method.fail_content(dpid, diff_list, subscriber_email)


    elif "failed" in transfer_output:
        logging.error('[ERROR] Something wrong during transfer, please check it')
        logging.error(transfer_output)
        logging.error("[ERROR] File Transfer is failed, please check it!!!")
        email_method.fail_content(dpid, diff_list, subscriber_email)

    logging.info("File Transfer is done")
    email_method.success_content(dpid, diff_list, subscriber_email)

    logging.info('Remove two files: host_trans_temp and gridftp_trans_file_temp')
    endtime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
    logging.info('transfer end time %s', endtime)
    host_trans_temp.close()
    gridftp_trans_file_temp.close()

def fts3_transfer(dpid, diff_list, subscriber_email):

    # Create a transfer_list with the source hostname and destination hostname
    # Perform fts3-transfer-submit command line
    # Remove transfer_list after the transfer is done

    updatetime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
    logging.info('transfer time %s', updatetime)
    file_num = len(diff_list)

    if fts_transfer.delegate(fts3_host, proxy_path) == True:
        filetransfer = fts_transfer.create_transferlist(dpid, diff_list)
        status_id = fts_transfer.submit(fts3_host, proxy_path, filetransfer)
        fts_query = fts_transfer.status(status_id, fts3_host, proxy_path)
        result = fts_query['query_status']
        all_info = fts_query['query_info']

        if result.count("FINISHED") == file_num:
            logging.info('Finished files are the same with the expected transferred files')
            logging.info("File Transfer is done")
            email_method.success_content(dpid, diff_list, subscriber_email)
            return True

        elif "SUBMITTED" in result:
            fts_query = fts_transfer.status(status_id, fts3_host, proxy_path)
            result = fts_query['query_status']
            all_info = fts_query['query_info']
            logging.info('FINISHED ITEMS ARE %s', result.count("FINISHED"))
            logging.info('SUBMITTED ITEMS ARE %s', result.count("SUBMITTED"))
            logging.info('FAILED ITEMS ARE %s', result.count("FAILED"))
            if fts_query.count("FINISHED") == file_num:
                logging.info('Finished files are the same with the expected transferred files')
                logging.info("File Transfer is done")
                email_method.success_content(dpid, diff_list, subscriber_email)
                return True
            elif "FAILED" in fts_query:
                logging.error('[ERROR] Something wrong during transfer, please check it')
                logging.error("[ERROR] File Transfer is failed, please check it!!!")
                email_method.fail_fts_content(dpid, diff_list, subscriber_email, result, all_info)
                return False
            else:
                logging.error('[ERROR] Something wrong during transfer, please check it')
                logging.error("[ERROR] File Transfer is failed, please check it!!!")
                email_method.fail_fts_content(dpid, diff_list, subscriber_email, result, all_info)
                return False

        else:
            logging.error('[ERROR] Something wrong during transfer, please check it')
            email_method.fail_fts_content(dpid, diff_list, subscriber_email, result, all_info)
            return False
    else:
        email_method.fail_fts_delegation(dpid, diff_list, subscriber_email)
        return False

#####REST Endpoint Functions#######

# Endpoint for validation of auth token and creation of session if user validated
# this is the only endpoint available without a decorator @login_required, meaning it is open and can be

@app.route('/api/v1.0/cli_auth', methods=['POST'])

def cli_auth():
    token = request.headers['token']# fetch the user authorized token from the client
    print token
    endpoint = "https://login.elixir-czech.org/oidc/userinfo?access_token="
    resp = requests.get(endpoint+token)
    user_data = json.loads(resp.text)# get user info from token
    print "this is user data"
    global user_email
    user_email = user_data['email']# extract email from userinfo
    print user_email
    username_token = user_data['preferred_username']
    print username_token
    print "this is username"
    if username_token is not None:
        session = crud(token, username_token, "create_session", '')
        print "this is sesson"
        print session
        return user_email + " authenticated!"
    else:
        return "Unable to authenticacte user"

@app.route('/api/v1.0/check_proxy', methods=['GET'])
@login_required
def check_proxy():

    serv_response = check_proxy_cert()
    logging.info('This is serv_response from check_proxy_cert() called from /check_proxy endpoint!')
    json_response = jsonify(serv_response)
    response = make_response(json_response)
    response.headers['Content-Type'] = "application/json"
    return response

@app.route('/api/v1.0/dataset/verify_file', methods=['GET'])
@login_required

def verify_files():

    dpid = request.form['dpid']
    return_msg = []
    if check_proxy_cert() == True:
        return_msg.append("Proxy Cert is valid!!!")
        verified = verify_file(dpid)
        return_msg.append(verified)
        response = '\n'.join(map(str, return_msg))
        return response
    else:
        logging.warning("[WARNING] GridFTP proxy certificate is not valid.!!!")
        return 'GridFTP proxy certificate is not valid.'

@app.route('/api/v1.0/dataset/datasetpid_existence', methods=['POST'])
@login_required
def datasetpid_existence(dpid):

    datasetpid_existence = crud('', dpid, "datasetpid_existence", '')
    if datasetpid_existence:
        return True
    else:
        logging.error('Dataset PID does not exist')
        return False

@app.route('/api/v1.0/dataset/username_existence', methods=['POST'])
@login_required
def username_existence(username):

    username_existence = crud('', '', "username_existence", username)
    if username_existence:
        return True
    else:
        logging.error('Username does not exist')
        return False

@app.route('/api/v1.0/dataset/verify', methods=['GET'])
@login_required
def verify():

    client_response = []
    client_data = request.data
    logging.info(request)
    dpid = request.form['dpid']
    version = request.form['version']

    if datasetpid_existence(dpid) == True:
        client_response.append('This datasetpid exists\n')

        # Will check file existence, checksum and release version
        if dpid and version != 'none':
            if check_proxy_cert() == True:
                # Check dataset version
                version_check = dataset_version_check(dpid)
                if version_check == "":
                    client_response.append('There is no released version information in DB\n')
                    logging.info('There is no released version information in DB')
                elif version == version_check:
                    client_response.append('Current released version is matched\n')
                    logging.info('Current released version is matched')
                else:
                    client_response.append(('Current released version {}, version is not matched. Previous version is {}\n').format(version, version_check))
                    logging.info('Current released version %s, version is not matched. Previous version is %s'.format(version, version_check))
                status = dataset_status_check(dpid)
                if status == "Open":
                    client_response.append('Dataset Status is Open and will verify the file existence\n')
                    logging.info('Dataset Status is Open and will verify the file existence')
                    verify_file_return = verify_file(dpid)
                    client_response.append(verify_file_return)

                elif status == "Released":
                    client_response.append('Dataset status is Released and will do integrity checking\n')
                    logging.info('Dataset status is Released and will do integrity checking')
                    integrity_check_return = integrity_check(dpid)
                    client_response.append(integrity_check_return)
                else:
                    client_response.append('Dataset status is not Open or Released Please check dataset status\n')
                    logging.info('Dataset status is not Open or Released Please check dataset status')
            else:
                logger.warning("[WARNING] Proxy certificate is not valid!!!")
                client_response.append('GridFTP proxy certificate not found.')
                client_response.append('Proxy certificate is not valid!!!')

        elif dpid and version == 'none':
            if check_proxy_cert() == True:
                status = dataset_status_check(dpid)

                if status == "Open":
                    client_response.append('Dataset status is Open and will verify the file existence\n')
                    logging.info('Dataset status is Open and will verify the file existence')
                    verify_file_return = verify_file(dpid)
                    client_response.append(verify_file_return)
                elif status == "Released":
                    client_response.append('Dataset status is Released and will do integrity checking\n')
                    logging.info('Dataset status is Released and will do integrity checking')
                    integrity_check_return = integrity_check(dpid)
                    client_response.append(integrity_check_return)
                else:
                    client_response.append('Dataset status is not Open or Released, please check dataset status\n')
                    logging.info('Dataset status is not Open or Released, please check dataset status')
            else:
                logger.warning("[WARNING] Proxy certificate is not valid!!!")
                client_response.append('Proxy certificate is not valid!!!')

        elif version:
            client_response.append('Please add DatasetPID information\n')
            logging.info('Need to add DatasetPID information')

        else:
            client_response.append('Please add the value\n')
            logging.info('Please add the value')

    else:
        client_response.append('This datasetpid does not exist\n')
        logging.error('This datasetpid does not exist')

    response = '\n'.join(map(str, client_response))
    return response


@app.route('/api/v1.0/dataset/diff_db_version', methods=['GET'])
@login_required
def diff_db_version():

    dpid = request.form['dpid']
    v1 = request.form['version1']
    v2 = request.form['version2']

    diff_result = []
    if datasetpid_existence(dpid) == True:
        diff_result.append('This datasetpid exists')
        diff_list1 = list_dataset(dpid, v1)
        diff_list2 = list_dataset(dpid, v2)
        dataset_diff = difflib.Differ()
        diff = dataset_diff.compare(diff_list1, diff_list2)
        diff_string = '\n'.join(diff)
        for line in diff_string.splitlines():
            if line.startswith("-"):
                diff_result.append(line)
        for line in diff_string.splitlines():
            if line.startswith("+"):
                diff_result.append(line)
        logging.info(sorted(diff_result))
    else:
        diff_result.append('This datasetpid does not exist')
        logging.error('This datasetpid does not exist')

    json_response = jsonify(diff_result)
    return json_response

@app.route('/api/v1.0/dataset/list/<dpid>', methods=['GET'])
@login_required
def list(dpid):

    serv_message = []
    if datasetpid_existence(dpid) == True:
        serv_message.append('This datasetpid exists')
        version = request.form['version']
        if version == '0':
            version = 'none'
            dataset_last_version = crud('', dpid, "get_dataset_last_version", '')
            dataset_version_int = dataset_last_version[0][0]
            current_working_dataset = dataset_last_version[0][0] + 1
            dataset_list = list_dataset(dpid, version)
            serv_message.append('Last released version is '+str(dataset_version_int))
            serv_message.append('Current working version is '+str(current_working_dataset))
            serv_message.append(dataset_list)
        else:
            serv_message = list_dataset(dpid, version)
    else:
        serv_message.append('This datasetpid does not exist')
        logging.error('This datasetpid does not exist')

    json_response = jsonify(serv_message)
    response = make_response(json_response)
    response.headers['Content-Type'] = "application/json"
    return response


@app.route('/api/v1.0/dataset/sub_list/<username>', methods=['GET'])
@login_required
def sub_list(username):

    # List the subscribed datasetPID
    # Status should be Active
    serv_message = []

    if username_existence(username) == True:
        serv_message.append('This username exists')
        sub_list = crud('', '', "sub_list", username)
        serv_message.append(sub_list)
    else:
        serv_message.append('This username does not exist')
        logging.error('%s this username does not exist', username)

    json_response = jsonify(serv_message)
    response = make_response(json_response)
    response.headers['Content-Type'] = "application/json"
    return json_response


@app.route('/api/v1.0/dataset/sub_list_detail/', methods=['GET'])
@login_required
def sub_list_detail():

    dpid = request.form['dpid']
    username = request.form['username']
    serv_message = []

    if datasetpid_existence(dpid) == True:
        serv_message.append('This datasetpid exists')
        serv_message = crud('', dpid, "sub_list_detail", username)

    else:
        serv_message.append('This datasetpid does not exist')
        logging.error('This datasetpid does not exist')

    json_response = jsonify(serv_message)
    response = make_response(json_response)
    response.headers['Content-Type'] = "application/json"
    return json_response

@app.route('/api/v1.0/register_single', methods=['POST'])
@login_required
def single_register():
    if not request.json:
        abort(400)
    d = request.json
    i = 1
    serv_message = crud(d, '', "reg_single", i)
    json_response = jsonify(serv_message)
    return json_response

@app.route('/api/v1.0/register_multiple', methods=['POST'])
@login_required
def multiple_register():
    if not request.json:
        abort(400)
    d = request.json
    final_response = []
    for i in range(len(d["Source"])):
        serv_message = crud(d, '', "reg_multiple", i)
        final_response.extend(serv_message)
    final_response = jsonify(final_response)
    return final_response


@app.route('/api/v1.0/unregister/<dpid>', methods=['PUT'])
@login_required
def unregister(dpid):

    client_response = []
    if datasetpid_existence(dpid) == True:
        client_response.append('This datasetpid exists')

        i = 1
        crud('', dpid, "unreg", i)
        client_response.append(dpid + str(' succesfully unregistered'))
        logging.info('%s succesfully unregistered', dpid)

    else:
        client_response.append('This datasetpid does not exist')
        logging.error('This datasetpid does not exist')

    response = '\n'.join(map(str, client_response))
    return response

@app.route('/api/v1.0/dataset/add_file/<dpid>', methods=['PUT'])
@login_required
def add_file(dpid):
    i = 1
    if not request.json:
        abort(400)
    d = request.json
    # add single file
    if (len(d["FileName"][0]) == 1 and len(d["DatasetPID"][0]) == 1):
        serv_message = crud(d, dpid, "add_file", i, d["FileName"])
        json_response = jsonify(serv_message)
        get_timestamp(dpid)

        return json_response

    # add multiple files to the dataset and print on the screen
    elif (len(d["FileName"][0]) != 1 and len(d["DatasetPID"][0]) == 1):
        for i in d["FileName"]:
            serv_message = crud(d, dpid, "add_files", i, d["FileName"])
            json_response = jsonify(serv_message)
            get_timestamp(dpid)

        return json_response

    # add multiple files to multiple datasets
    elif (len(d["FileName"][0]) != 1 and len(d["DatasetPID"][0]) != 1):
        logging.warning('[WARNING] Multiple files to: multiple datasets are not yet supported!!')

def fremotefile_exist_check(dpid):

    file_path = crud('', dpid, "file_location", '')
    final_result = []

    for row in file_path:
        hostname = row[2]
        folder = row[1]
        keepalive_cmd = "-keepalive 150"
        recursive_cmd = "dir -r"
        cmd = """uberftp %s %s "%s %s"  """ % (hostname, keepalive_cmd, recursive_cmd, folder)
        status, queryfile_output = commands.getstatusoutput(cmd)
        files = queryfile_output.split("\n")
        pattern = '((\/.*\.)({}))'.format(suffix)

        for l in files:
            result = re.search(pattern, l)
            if result:
                logging.info('Show remote file name and timestamp')
                logging.info(result.group(1))
                timestamp = timestamp_check(result.group(1), hostname)
                final_result.append((result.group(1), timestamp))
        return final_result

def DBfile_check(dpid):

    dataset_last_version = crud('', dpid, "get_dataset_last_version", '')
    dataset_version_int = dataset_last_version[0][0]
    file_info = crud('', dpid, "file_info_DBfile_check", '')

    reply = []
    for file_num in file_info:
        reply.append(file_num)
    final_response = reply
    return final_response

def collect_file_list(filename):

    if filename in file_list:
        ###This file is already on the list, don't need to add it
        logging.info('This file %s is already on the list, dont need to add it', filename)
        pass
    else:
        ###only add new file
        file_list.append(filename)
    return file_list

def query_folder(folder_path):

    list_cmd = "-list"
    path_cmd = folder_path
    cmd = """globus-url-copy %s %s  """ % (list_cmd, path_cmd)
    status, queryfile_output = commands.getstatusoutput(cmd)
    files = queryfile_output.split("\n")
    compare_folder_or_file(files)

def compare_folder_or_file(files):

    for query_info in files[1:]:
        folder_name = query_info.replace(" ", "")
        folder_path = files[0] + folder_name
        ### / in the end, it means this is a folder not a file
        if query_info[-1:] == "/":
            query_folder(folder_path)

        elif query_info[-1:] == "":
            pass
        else:
            result = re.search(pattern, files[0])
            if result:
                filename = (result.group(1))+folder_name
            collect_file_list(filename)

def check_file_folder_path(hostname, full_path):

    recursive_cmd = "dir"
    cmd = """uberftp %s "%s %s"  """ % (hostname, recursive_cmd, full_path)
    status, queryfile_output = commands.getstatusoutput(cmd)

    if "error" in queryfile_output:
        logging.error('Folder or File path does not match')
        logging.error(queryfile_output)
        return False
    elif "No match" in queryfile_output:
        logging.error('Folder or File path does not match')
        logging.error(queryfile_output)
        return False
    elif "500 Command failed" in queryfile_output:
        logging.error('Folder or File path does not match')
        logging.error(queryfile_output)
        return False
    elif "failed" in queryfile_output:
        logging.error('Folder or File path does not match')
        logging.error(queryfile_output)
        return False
    else:
        return True

@app.route('/api/v1.0/dataset/index_folder', methods=['POST'])
@login_required
def index_folder():

    # Get file locations and compare if there is any foldername
    dpid = request.form['dpid']
    foldername = request.form['foldername']
    final_result = []
    remotefile_list = []
    file_total = 0

    if datasetpid_existence(dpid) == True:
        final_result.append('This datasetpid exists')

        if check_proxy_cert() == True:
            if foldername:
                logging.info('There is a foldername %s', foldername)
                # Get file path from DB
                file_path = crud('', dpid, "file_location", '')
                # get list of existing files in db and the last dataset version
                db_files = list_dataset(dpid, 'none')
                # If there is no file in DB
                if not db_files:
                    db_files = '#'
                # Query remote site information via uberftp command
                add_file = ''
                delete_file = ''

                for row in file_path:
                    hostname = row[2]
                    full_path = foldername
                    list_cmd = "-list"
                    gsi_cmd = "gsiftp://"
                    port_cmd = ":2811"
                    cmd = """globus-url-copy %s %s%s%s%s  """ % (list_cmd, gsi_cmd, hostname, port_cmd, full_path)

                    if check_file_folder_path(hostname, full_path) == True:
                        logging.info('File/Folder Path is Correct!!!')
                        status, queryfile_output = commands.getstatusoutput(cmd)
                        files = queryfile_output.split("\n")

                        msg = ''
                        for l in files[1:]:
                            folder_name = l.replace(" ", "")
                            folder_path = files[0] + folder_name
                            ### / in the end, it means this is a folder not a file
                            if l[-1:] == "/":
                                query_folder(folder_path)
                            elif l[-1:] == "":
                                pass
                            else:
                                filename = full_path + folder_name
                                collect_file_list(filename)

                        for single_file in file_list:
                            file_total += 1
                            if single_file not in db_files:
                                # import file names to DB
                                logging.info('%s this file does not exist in DB, will add it', single_file)
                                add_file = single_file
                            if single_file in db_files:
                                msg = single_file, "File is already in Database !!!"
                            final_result.extend(msg)
                            msg = ''

                            if add_file:
                                # add file only if file not already deleted for current working version
                                # should be checked if we have many deleted files
                                dataset_last_version = crud('', dpid, "get_dataset_last_version", '')
                                dataset_version_int = dataset_last_version[0][0]
                                dataset_working_version = dataset_version_int + 1
                                deleted_file = crud(dataset_working_version, dpid, 'get_deleted_files', '')
                                if deleted_file:
                                    if add_file not in deleted_file:
                                        remote_filenames = crud(dataset_working_version, dpid, "index_add_files", '', add_file)
                                        final_result.extend(remote_filenames)

                                    else:
                                        logging.warning('%s not adding already marked deleted file', add_file)
                                else:
                                    remote_filenames = crud(dataset_working_version, dpid, "index_add_files", '', add_file)
                                    final_result.extend(remote_filenames)
                                    add_file = ''
                                    # Files should not be deleted
                                    # If this file is in DB but not in remote site, delete it

                            # If this file is in DB but not in remote site, delete it
                        delete_list = []
                        for n in db_files:
                            if n not in file_list:
                                logging.warning("[WARNING] %s this file is not here!!!", n)
                                delete_list.append(n)
                            else:
                                continue
                        for list in delete_list:
                            file_id = crud('', dpid, "file_id", list)
                            if file_id:
                                for name in file_id:
                                    file_id = name[0]
                                    delete_file = crud('', dpid, "delete_file", file_id)
                                logging.info('%s this file is deleted', delete_file)
                            else:
                                logging.warning("There is no File_id!! This file does not exist!!")
                        final_result = jsonify(final_result)
                        get_timestamp(dpid)

                        if final_result:
                            return final_result
                        else:
                            logging.warning('No new files indexed!')
                            return jsonify("No new files indexed!")
                    else:
                        final_result.append("This file/folder path is not correct!!! Please check it")
                        logging.error('This file/folder path is not correct!!! Please check it')
                        json_response = jsonify(final_result)
                        return json_response

            else:
                logging.warning("Can't get foldername information")

        else:
            logger.warning("[WARNING] GridFTP proxy certificate is not valid.!!!")
            final_result.append('GridFTP proxy certificate is not valid.')
            json_response = jsonify(final_result)
            return json_response
    else:
        final_result.append('This datasetpid does not exist')
        logging.error('%s this datasetpid does not exist', dpid)
        json_response = jsonify(final_result)
        return json_response

@app.route('/api/v1.0/dataset/index', methods=['POST'])
@login_required
def index():

    dpid = request.form['dpid']
    logging.info('There is no foldername')

    final_result = []
    remotefile_list = []
    file_total = 0

    if datasetpid_existence(dpid) == True:
        final_result.append('This datasetpid exists')

        if check_proxy_cert() == True:
            file_path = crud('', dpid, "file_location", '')
            db_files = list_dataset(dpid, 'none')
            # If there is no file in DB
            if not db_files:
                db_files = '#'
            add_file = ''
            for row in file_path:
                hostname = row[2]
                full_path = row[1]
                list_cmd = "-list"
                gsi_cmd = "gsiftp://"
                port_cmd = ":2811"
                cmd = """globus-url-copy %s %s%s%s%s  """ % (list_cmd, gsi_cmd, hostname, port_cmd, full_path)
                check_file_folder_path(hostname, full_path)

                if check_file_folder_path(hostname, full_path) == True:
                    logging.info('File/Folder Path is Correct!!!')
                    status, queryfile_output = commands.getstatusoutput(cmd)
                    files = queryfile_output.split("\n")

                    msg = ''

                    for l in files[1:]:
                        folder_name = l.replace(" ", "")
                        folder_path = files[0] + folder_name
                        ### / in the end, it means this is a folder not a file
                        if l[-1:] == "/":
                            query_folder(folder_path)
                        elif l[-1:] == "":
                            pass
                        else:
                            filename = full_path + folder_name
                            collect_file_list(filename)

                    for single_file in file_list:
                        file_total += 1

                        if single_file not in db_files:
                            # import file names to DB
                            logging.info('%s this file does not exist in DB, will add it', single_file)
                            add_file = single_file
                        if single_file in db_files:
                            msg = single_file, "File is already in Database !!!"
                        final_result.extend(msg)
                        msg = ''

                        if add_file:
                            # add file only if file not already deleted for current working version
                            # should be checked if we have many deleted files
                            dataset_last_version = crud('', dpid, "get_dataset_last_version", '')
                            dataset_version_int = dataset_last_version[0][0]
                            dataset_working_version = dataset_version_int +  1
                            deleted_file = crud(dataset_working_version, dpid, 'get_deleted_files', '')

                            if deleted_file:
                                if add_file not in deleted_file:
                                    remote_filenames = crud(dataset_working_version, dpid, "index_add_files", '', add_file)
                                    final_result.extend(remote_filenames)

                                else:
                                    logging.warning('%s not adding already marked deleted file', add_file)
                            else:
                                remote_filenames = crud(dataset_working_version, dpid, "index_add_files", '', add_file)
                                final_result.extend(remote_filenames)
                                add_file = ''
                    # Files should not be deleted
                    # If this file is in DB but not in remote site, delete it
                    delete_list = []
                    for n in db_files:
                        if n not in file_list:
                            logging.warning("[WARNING] %s this file is not here!!!", n)
                            delete_list.append(n)
                        else:
                            continue
                    for list in delete_list:
                        final_result.append(list)

                    print "final_result", final_result
                    final_result = jsonify(final_result)
                    get_timestamp(dpid)

                    if final_result:
                        return final_result
                    else:
                        logging.warning('No new files indexed!')
                        return jsonify("No new files indexed!")

                else:
                    final_result.append("This file/folder path is not correct!!! Please check it")
                    logging.error('This file/folder path is not correct!!! Please check it')
                    json_response = jsonify(final_result)
                    return json_response


        else:
            logging.warning("[WARNING] GridFTP proxy certificate is not valid.!!!")
            final_result.append('GridFTP proxy certificate is not valid.')
            json_response = jsonify(final_result)
            return json_response

    else:
        final_result.append('This datasetpid does not exist')
        logging.error('This datasetpid does not exist')
        json_response = jsonify(final_result)
        return json_response

@app.route('/api/v1.0/dataset/file_id_check', methods=['GET'])
@login_required
def file_id_check():

    dpid = request.form['dpid']
    filepath = request.form['filepath']
    file_id = crud('', dpid, "file_id", filepath)

    if file_id:
        for name in file_id:
            file_id = name[0]
            return file_id
    else:
        logging.warning("There is no Fileid!! This file does not exist!!")

@app.route('/api/v1.0/dataset/dataset_status_check', methods=['POST'])
@login_required
def dataset_status_chk():

    dpid = request.form['dpid']
    client_response = []
    if datasetpid_existence(dpid) == True:
        client_response = dataset_status_check(dpid)
        return client_response
    else:
        logging.error('%s this datasetpid does not exist', dpid)
        return "This datasetpid does not exist"

def dataset_version_check(dpid):
# Check dataset status and return the result to the client side let users choose to delete or not

    dataset_status = crud('', dpid, "dataset_status", '')
    for status in dataset_status:
        version_result = status[1]
        return str(version_result)

@app.route('/api/v1.0/dataset/release_version_check', methods=['POST'])
def release_version_check():

    dpid = request.form['dpid']
    dataset_status = crud('', dpid, "dataset_status", '')
    for status in dataset_status:
        version_result = status[1]
    return str(version_result)

@app.route('/api/v1.0/dataset/file_version_check', methods=['POST'])
@login_required
def file_version_check():

    dpid = request.form['dpid']
    filename = request.form['filename']
    get_file_last_version = crud('', dpid, "get_file_last_version", filename)
    get_file_last_version_int = get_file_last_version[0][0]
    return str(get_file_last_version_int)

def get_checksum(dpid, diff_list):

    updatetime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
    logging.info('Get checksum time %s', updatetime)

    file_path = crud('', dpid, "file_location", '')

    for filepath in diff_list:
        for row in file_path:
            hostname = row[2]
            checksum_cmd = "quote cksm md5 0 -1"
            cmd = """uberftp %s "%s %s"  """ % (hostname, checksum_cmd, filepath)
            status, checksum_output = commands.getstatusoutput(cmd)
            checksum_lines = StringIO.StringIO(checksum_output)
            lines = checksum_lines.readlines()
            myline = lines[2]
            checksum = myline.split()[1]
            update_checksum = crud('', checksum, "update_checksum", filepath)
            logging.info('Update Checksum %s', update_checksum)
    return "updating_checksum"


def get_filesize(dpid, diff_list):

    updatetime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
    logging.info('Get filesize time %s', updatetime)

    file_path = crud('', dpid, "file_location", '')

    for filepath in diff_list:
        for row in file_path:
            hostname = row[2]
            filesize_cmd = "size"
            cmd = """uberftp %s "%s %s"  """ % (hostname, filesize_cmd, filepath)
            status, filesize_output = commands.getstatusoutput(cmd)
            filesize_lines = StringIO.StringIO(filesize_output)
            lines = filesize_lines.readlines()
            filesize = lines[2]
            update_filesize = crud('', filesize, "update_filesize", filepath)
            logging.info('update_filesize %s', update_filesize)
    return "update_filesize"


def get_timestamp(dpid):

    dpid = request.form['dpid']
    file_info = crud('', dpid, "file_info", '')
    file_path = crud('', dpid, "file_location", '')

    for file in file_info:
        filepath = file[1]

        for row in file_path:
            hostname = row[2]
            keepalive_cmd = "-keepalive 150"
            recursive_cmd = "dir -r"
            cmd = """uberftp %s %s "%s %s"  """ % (hostname, keepalive_cmd, recursive_cmd, filepath)
            status, timestamp_output = commands.getstatusoutput(cmd)
            timestamp_lines = StringIO.StringIO(timestamp_output)
            lines = timestamp_lines.readlines()
            timestamp_line = lines[2]
            files = timestamp_line.split()[-4:]
            gridftp_timestamp = ' '.join(files[0:3])

            update_gridftp_timestamp = crud('', gridftp_timestamp, "update_gridftp_timestamp", filepath)
#            logging.info('update_gridftp_timestamp', update_gridftp_timestamp)
#    logging.info('update_gridftp_timestamp %s ', update_gridftp_timestamp)
#    return("update_timestamp")

def timestamp_check(file, hostname):

    keepalive_cmd = "-keepalive 150"
    recursive_cmd = "dir -r"
    cmd = """uberftp %s %s "%s %s"  """ % (hostname, keepalive_cmd, recursive_cmd, file)
    status, timestamp_output = commands.getstatusoutput(cmd)
    timestamp_lines = StringIO.StringIO(timestamp_output)
    lines = timestamp_lines.readlines()
    timestamp_line = lines[2]
    files = timestamp_line.split()[-4:]
    gridftp_timestamp = ' '.join(files[0:3])
    return gridftp_timestamp

def integrity_check(dpid):

    message = []
    file_info = crud('', dpid, "file_info", '')
    file_path = crud('', dpid, "file_location", '')

    filelist = []
    for file in file_info:
        filepath = file[1]
        for row in file_path:
            hostname = row[2]
            checksum_cmd = "quote cksm md5 0 -1"
            cmd = """uberftp %s "%s %s"  """ % (hostname, checksum_cmd, filepath)
            status, checksum_output = commands.getstatusoutput(cmd)
            checksum_debug = checksum_output.split()
            checksum_lines = StringIO.StringIO(checksum_output)
            lines = checksum_lines.readlines()
            myline = lines[2]
            checksum = myline.split()[1]

            file_checksum = crud('', dpid, "file_checksum", filepath)

            for num in file_checksum:
                filechecksum_db = num[0]
                if filechecksum_db == checksum:
                    message = "Checksum Match!!"
                    continue

                else:
                    message = "Checksum Not match!! Please check this file\n", filepath
                    logging.warning("Checksum Not match!! Please check this file\n")
                    filelist.append(filepath)

    print filelist
    return message

def checksum_check(dpid, file):

    message = []
    logging.info('Checking single file Checksum')
    file_path = crud('', dpid, "file_location", '')
    for row in file_path:
        hostname = row[2]
        checksum_cmd = "quote cksm md5 0 -1"
        cmd = """uberftp %s "%s %s"  """ % (hostname, checksum_cmd, file)
        status, checksum_output = commands.getstatusoutput(cmd)
        checksum_debug = checksum_output.split()
        checksum_lines = StringIO.StringIO(checksum_output)
        lines = checksum_lines.readlines()
        myline = lines[2]
        checksum = myline.split()[1]

        file_checksum = crud('', dpid, "file_checksum", file)

        for num in file_checksum:
            filechecksum_db = num[0]
            # Checksum should be empty on initial index, after dataset release, checksum should be added into local DB.
            # Compare dataset status is open, it should be initial index or afterwards index
            if filechecksum_db == '':
                logging.info('There is no checksum information to compare')
                dataset_last_version = crud('', dpid, "get_dataset_last_version", '')
                dataset_version_int = dataset_last_version[0][0]
                if dataset_version_int == 0:
                    message = "No checksum because this dataset is initial and does not release yet.\n"
                    logging.warning("No checksum because this dataset is initial and does not release yet.\n")
                else:
                    message = "This dataset was release before but there is no checksum recorded into DB. Please check the checksum of file\n"
                    logging.warning("This dataset was release before but there is no checksum recorded into DB. Please check the checksum of file\n")
            else:
                if filechecksum_db == checksum:
                    message = "Checksum Match!!\n"
                    continue
                else:
                    message = "Checksum Not match!! Please check this file" + file + "\n"
                    logging.warning("Checksum Not match!! Please check this file %s", file)
    return message

@app.route('/api/v1.0/dataset/release_dataset', methods=['POST'])
@login_required
def release_dataset():

    #update the dataset status in DB
    dpid = request.form['dpid']
    version = request.form['version']
    update_release_status = crud('', dpid, "update_release_status", version)
    logging.info('Update Release Status is %s', update_release_status)

    ########## subscription notifications
    # gets all subscriptions
    # checks if current dataset to be released is in subscriptions
    # sends an email only to subscribers who subscribed to currently released dataset
    subscriptions = get_subscription()
    for row in subscriptions:
        subscriber_dataset = row[1]
        if subscriber_dataset == dpid:
            logging.info('Subscriber_dataset and current released dataset match')
            subscriber_email = row[2]
            subscriber_username = row[3]
            dataset_last_version = crud('', subscriber_dataset, "get_dataset_last_version", '')
            dataset_last_version_int = dataset_last_version[0][0]

            dpid = subscriber_dataset
            v2 = dataset_last_version_int
            v1 = dataset_last_version_int

            diff_list = diff(dpid, v1, v2)
            logging.info('diff for last two releases')
            logging.info(diff_list)

            get_checksum(dpid, diff_list)
            get_filesize(dpid, diff_list)

            email_method.start_transfer_email(subscriber_dataset, diff_list, subscriber_email)

            ### Compare which port that subscriber provides (gridftp: 2811, FTS3: 8446, HTTPS: 8443, SRMv2: 8443)
            transfer_port_choice = crud(subscriber_username, '', "transfer_port_choice", '')
            logging.info('Subscriber port is %s', transfer_port_choice[0][0])

            if transfer_port_choice[0][0] == "2811":
                logging.info('Will use globus url copy to transfer files')
                data_transfer(dpid, diff_list, subscriber_email)
            elif transfer_port_choice[0][0] == "8446":
                logging.info('Will use FTS3 to transfer files')
                fts3_transfer(dpid, diff_list, subscriber_email)
            # Other ports will choose FTS3 by default
            else:
                logging.info('Will use FTS3 to transfer files')
                fts3_transfer(dpid, diff_list, subscriber_email)

        else:
            pass
    update_release_status = crud('', dpid, "update_release_status", version)
    json_response = jsonify(update_release_status)
    return json_response


@app.route('/api/v1.0/dataset/release_dataset_without_version', methods=['POST'])
@login_required
def release_dataset_without_version():

    # update the dataset status in DB
    dpid = request.form['dpid']
    #### There is no release version, so we should get the latest dataset working version here
    dataset_version = crud('', dpid, "get_dataset_last_version", '')
    dataset_version_int = dataset_version[0][0]
    dataset_working_version = dataset_version_int + 1
    logging.info('dataset current working version is %s', dataset_working_version)

    update_release_status = crud('', dpid, "update_release_status", dataset_working_version)
    logging.info('Update Release Status is %s', update_release_status)

    ########## subscription notifications
    # gets all subscriptions
    # checks if current dataset to be released is in subscriptions
    # sends an email only to subscribers who subscribed to currently released dataset
    subscriptions = get_subscription()
    for row in subscriptions:
        subscriber_dataset = row[1]
        if subscriber_dataset == dpid:
            logging.info('Subscriber_dataset and current released dataset match')
            subscriber_email = row[2]
            subscriber_username = row[3]
            dataset_last_version = crud('', subscriber_dataset, "get_dataset_last_version", '')
            dataset_last_version_int = dataset_last_version[0][0]

            dpid = subscriber_dataset
            v2 = dataset_last_version_int
            v1 = dataset_last_version_int

            diff_list = diff(dpid, v1, v2)
            logging.info('diff for last two releases')
            logging.info(diff_list)

            get_checksum(dpid, diff_list)
            get_filesize(dpid, diff_list)

            email_method.start_transfer_email(subscriber_dataset, diff_list, subscriber_email)

            ### Compare which port that subscriber provides (gridftp: 2811, FTS3: 8446, HTTPS: 8443, SRMv2: 8443)
            transfer_port_choice = crud(subscriber_username, '', "transfer_port_choice", '')
            logging.info('Subscriber port is %s', transfer_port_choice[0][0])

            if transfer_port_choice[0][0] == "2811":
                logging.info('Will use globus url copy to transfer files')
                data_transfer(dpid, diff_list, subscriber_email)
            elif transfer_port_choice[0][0] == "8446":
                logging.info('Will use FTS3 to transfer files')
                fts3_transfer(dpid, diff_list, subscriber_email)
            # Other ports will choose FTS3 by default
            else:
                logging.info('Will use FTS3 to transfer files')
                fts3_transfer(dpid, diff_list, subscriber_email)
        else:
            pass

    update_release_status = crud('', dpid, "update_release_status", dataset_working_version)
    json_response = jsonify(update_release_status)
    return json_response

@app.route('/api/v1.0/dataset/delete', methods=['DELETE'])
@login_required
def delete():

    try:
        dpid = request.form['dpid']
        filepath = request.form['filepath']
        file_id = crud('', dpid, "file_id", filepath)
        if file_id:
            logging.info('[DELETE] this is file_id %s', file_id)
        else:
            logging.error('%s this filePath is incorrect', filepath)
            return "This filePath is incorrect"

        dataset_last_version = crud('', dpid, "get_dataset_last_version", '')
        dataset_version_int = dataset_last_version[0][0]
        dataset_working_version = dataset_version_int + 1
        if file_id:
            for name in file_id:
                file_id = name[0]
                delete_file = crud(dataset_working_version, dpid, "delete_file", file_id)
            return delete_file
        else:
            logging.warning("There is no File_id!! This file does not exist!!")
            return "There is no File_id,  This file does not exist!!"
    except:
        logging.warning("There is no datasetPID or FilePath")
        return "There is no datasetPID or FilePath"

@app.route('/api/v1.0/add_subscriber', methods=['POST'])
@login_required
def add_subscriber():

    if not request.json:
        abort(400)
    d = request.json
    subscriber_list = crud('', '', "list_subscriber", '')
    if not subscriber_list:
        subscriber_list = '#'
    add_subscriber = []
    msg = ''

    for name in subscriber_list:
        username = name[0]

    if username == d["Username"]:
        msg = d["Username"], " is already in Database !!!"
        logging.info(msg)
        add_subscriber.append(msg)
        msg = ''
    else:
        logging.warning(("%s This subscriber is not in DB, will add it") % (username))
        add_subscriber = crud(d, '', "add_subscriber", d["Username"])

    json_response = jsonify(add_subscriber)
    logging.info(json_response)
    return json_response

@app.route('/api/v1.0/activate_subscriber', methods=['POST'])
@login_required
def activate_subscriber():
    # This action is to activate the deleted subscriber, then he/she can re-subscribe datasets

    username = request.form['username']
    status = []

    activate_status = crud('', '', "activate_subscriber", username)
    if activate_status == True:
        status.append("This subscriber is already listed and status is active again")

    else:
        logging.warning("Activate is not working, please check it!!!")
        status.append("Activate is not working, please check it!!!")

    json_response = jsonify(status)
    logging.info(json_response)
    return json_response

@app.route('/api/v1.0/del_subscriber', methods=['DELETE'])
@login_required
def del_subscriber():
    # If this subscriber is deleted, the relationship of previous subscribed datasets are deleted

    username = request.form['username']
    if username_existence(username) == True:
        logging.info('%s this username exists', username)
        try:
#            delete_subscriber = crud('', '', "delete_subscriber", username)
#            return delete_subscriber
            return True
        except:
            logging.warning('There is no username')
            return "There is no username"
    else:
        logging.error('% this username does not exist, username')
        return "This username does not exist"


@app.route('/api/v1.0/dataset/subscriber_status', methods=['POST'])
@login_required
def subscriber_status():

    username = request.form['username']
    if username_existence(username) == True:
        logging.info('%s this username exists', username)
        subscriber_status = crud('', '', "subscriber_status", username)
        for status in subscriber_status:
            status_result = status[0]
            logging.info('subscriber status: %s', status_result)
            return status_result
    else:
        logging.error('%s this username does not exist', username)
        return "Error"

@app.route('/api/v1.0/subscribe_user', methods=['POST'])
@login_required
def subscribe_user():

    username = request.form['username']
    dpid = request.form['dpid']

    subscribe_status = []

    if datasetpid_existence(dpid) == True:
        subscribe_status.append('This datasetpid exists')

        if check_proxy_cert() == True:
            try:
                subscribe_user = crud('', dpid, "subscribe_user", username)
                if subscribe_user == True:
                    subscribe_status.append('This user and dataset are already subscribed!!!')
                    logging.info('This user %s and dataset %s are already subscribed!!!', username, dpid)
                else:
                    logging.warning('Subscription is not working, because the same data is in DB!!!')
                    subscribe_status.append('Subscription is not working, because the same data is in DB!!!')
            except:
                logging.error('There is a problem to subscribe_user')
                subscribe_status.append('There is a problem to subscribe_user')
        else:
            logger.warning("[WARNING] Proxy certificate is not valid")
            subscribe_status.append('Please use grid-proxy-init command line to generate a proxy certificate!!!')

    else:
        subscribe_status.append('This datasetpid does not exist')
        logging.error('% this datasetpid does not exist', dpid)

    json_response = jsonify(subscribe_status)
    logging.info(json_response)
    return json_response

@app.route('/api/v1.0/unsubscribe_user', methods=['POST'])
@login_required
def unsubscribe_user():

    username = request.form['username']
    dpid = request.form['dpid']

    unsubscribe_status = []

    if datasetpid_existence(dpid) == True:
        unsubscribe_status.append('This datasetpid exists')

        try:
            unsubscribe_user = crud('', dpid, "unsubscribe_user", username)

            if unsubscribe_user == True:
                unsubscribe_status.append('This user and dataset are already unsubscribed!!!')
                logging.info('This user %s and dataset %s are already unsubscribed!!!', username, dpid)
            else:
                logging.warning("Unsubscription is not working, please check it!!!")
                unsubscribe_status.append('Unsubscription is not working, please check it!!!')
        except:
            logging.warning("There is a problem to unsubscribe_user")
            unsubscribe_status.append('There is a problem to unsubscribe_user')

    else:
        unsubscribe_status.append('This datasetpid does not exist')
        logging.error('% this datasetpid does not exist', dpid)

    json_response = jsonify(unsubscribe_status)
    logging.info(json_response)
    return json_response

@app.route('/api/v1.0/subscription_check', methods=['POST'])
@login_required
def subscription_check():

    username = request.form['username']
    dpid = request.form['dpid']

    status = dataset_status_check(dpid)

    sub_email = crud('', '', "get_one_sub_email", username)
    for email in sub_email:
        subscriber_email = email[0]

    if status == "Open":
        ### Will check if there is previous release version
        dataset_last_version = crud('', dpid, "get_dataset_last_version", '')
        dataset_version_int = dataset_last_version[0][0]
        logging.info('Previous Version is: %s', dataset_version_int)

        if dataset_version_int == 0:
            logging.info('There is no previous release version, so files will be transferred when the dataset releases')
            return "There is no previous release version, so files will be transferred when the dataset releases"
        else:
            version = dataset_version_int
            transfer_list = crud(dataset_version_int, dpid, "list_dataset", '')

            ### Compare which port that subscriber provides (gridftp: 2811, FTS3: 8446, HTTPS: 8443, SRMv2: 8443)
            transfer_port_choice = crud(username, '', "transfer_port_choice", '')
            logging.info('Subscriber port is %s', transfer_port_choice[0][0])

            if transfer_port_choice[0][0] == "2811":
                logging.info('Will use globus url copy to transfer files')
                result = single_person_transfer(dpid, transfer_list, username)
                if result == True:
                    logging.info('File Transfer is done')
                    return "File Transfer is done"
                else:
                    logging.error('File Transfer has a problem, please check it!')
                    return "File Transfer has a problem, please check it!"
            elif transfer_port_choice[0][0] == "8446":
                logging.info('Will use FTS3 to transfer files')
                result = fts3_transfer(dpid, transfer_list, subscriber_email)
                if result == True:
                    logging.info('File Transfer is done')
                    return "File Transfer is done"
                else:
                    logging.error('File Transfer has a problem, please check it!')
                    return "File Transfer has a problem, please check it!"
            # other ports will choose FTS3 for transfer by default
            else:
                logging.info('Will use FTS3 to transfer files')
                result = fts3_transfer(dpid, transfer_list, subscriber_email)
                if result == True:
                    logging.info('File Transfer is done')
                    return "File Transfer is done"
                else:
                    logging.error('File Transfer has a problem, please check it!')
                    return "File Transfer has a problem, please check it!"

    elif status == "Released":
        ### Get the release version, then transfer all current files from the remote site
        dataset_last_version = crud('', dpid, "get_dataset_last_version", '')
        dataset_version_int = dataset_last_version[0][0]
        logging.info('Previous Version is: %s', dataset_version_int)

        version = dataset_version_int
        transfer_list = crud(dataset_version_int, dpid, "list_dataset", '')

        ### Compare which port that subscriber provides (gridftp: 2811, FTS3: 8446, HTTPS: 8443, SRMv2: 8443)
        transfer_port_choice = crud(username, '', "transfer_port_choice", '')
        logging.info('Subscriber port is %s', transfer_port_choice[0][0])

        if transfer_port_choice[0][0] == "2811":
            logging.info('Will use globus url copy to transfer files')
            result = single_person_transfer(dpid, transfer_list, username)
            if result == True:
                logging.info('File Transfer is done')
                return "File Transfer is done"
            else:
                logging.error('File Transfer has a problem, please check it!')
                return "File Transfer has a problem, please check it!"
        elif transfer_port_choice[0][0] == "8446":
            logging.info('Will use FTS3 to transfer files')
            result = fts3_transfer(dpid, transfer_list, subscriber_email)
            if result == True:
                logging.info('File Transfer is done')
                return "File Transfer is done"
            else:
                logging.error('File Transfer has a problem, please check it!')
                return "File Transfer has a problem, please check it!"
        # other ports will choose FTS3 for transfer by default
        else:
            logging.info('Will use FTS3 to transfer files')
            result = fts3_transfer(dpid, transfer_list, subscriber_email)
            if result == True:
                logging.info('File Transfer is done')
                return "File Transfer is done"
            else:
                logging.error('File Transfer has a problem, please check it!')
                return "File Transfer has a problem, please check it!"
    else:
        logging.warning('Dataset status is not Open or Released Please check dataset status')
        return "Dataset status is not Open or Released Please check dataset status"

def single_person_transfer(dpid, transfer_list, username):

    # This situation is when single person subscribes one dataset, if this dataset has previous release version, files should be transferred to target site
    # Create a host_temp with the source hostname and destination hostname
    # Create a gridftp_file_temp with the file names
    # Perform globus-url-copy command line (Gridftp)
    # Remove two files after the transfer is done

    updatetime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
    logging.info('transfer time %s', updatetime)

    file_path = crud('', dpid, "file_location", '')
    sourcelist = []
    for row in file_path:
        hostname = row[2]

    sub_list = crud('', '', "get_one_sub_host", username)
    for host in sub_list:
        destination_list = host[0]
        folder_path = host[1]

        sourcelist.append('@source' + '\n' + hostname + '\n' + '@destination' + '\n' + destination_list)

    ### Create a temp file for host and gridftp_file
    host_temp = tempfile.NamedTemporaryFile()
    gridftp_file_temp = tempfile.NamedTemporaryFile()
    try:
        logging.info('hostname: %s', host_temp)
        logging.info('hostname file name: %s', host_temp.name)
        host_temp.writelines(sourcelist)
        host_temp.seek(0)
        sourceurl = host_temp.name

        targetlist = []
        logging.info('Total files are %s', len(transfer_list))
        for n in transfer_list:

            targetlist.append("gsiftp://" + n + "  gsiftp://" + folder_path + n + n.split("/")[-1] + '\n')

        logging.info('filelist temp: %s', gridftp_file_temp)
        logging.info('filelist file name: %s', gridftp_file_temp.name)
        gridftp_file_temp.writelines(targetlist)
        gridftp_file_temp.seek(0)

        destinationurl = gridftp_file_temp.name

        # Command line sample: globus-url-copy -rst -p 50 -af hosts.txt -f gsiftp_file.txt
        verbose_mode = "-rst -p 50 -af"
        verbose_1_mode = '-cd -f'
        transfer_cmd = """globus-url-copy %s %s %s %s """ % (verbose_mode, sourceurl, verbose_1_mode, destinationurl)

        status, transfer_output = commands.getstatusoutput(transfer_cmd)

        ### Get subsciber email
        sub_email = crud('', '', "get_one_sub_email", username)
        for email in sub_email:
            subscriber_email = email[0]

        if "error" in transfer_output:
            logging.error('[ERROR] Something wrong during transfer, please check it')
            logging.error(transfer_output)
            logging.error("[ERROR] File Transfer is failed, please check it!!!")
            email_method.fail_content(dpid, transfer_list, subscriber_email)

        elif "failed" in transfer_output:
            logging.error('[ERROR] Something wrong during transfer, please check it')
            logging.error(transfer_output)
            logging.error("[ERROR] File Transfer is failed, please check it!!!")
            email_method.fail_content(dpid, transfer_list, subscriber_email)

        logging.info("File Transfer is done")
        email_method.success_content(dpid, transfer_list, subscriber_email)

    finally:
        logging.info('Remove two files: host_temp and gsiftp_file_temp')
        endtime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
        logging.info('transfer end time %s', endtime)
        host_temp.close()
        gridftp_file_temp.close()

