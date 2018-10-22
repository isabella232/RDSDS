#!/usr/bin/python
# Database operation function

from datetime import date, datetime
import random
import time
#from dsds_rest_service import *
import logging
import os
import psycopg2
from db_config import config


# Log setting and generate a logfile on the current place
logpath = os.getcwd() + "/dsds_server_logs"
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(message)s', filename=logpath)
logger = logging.getLogger('dsds_server_logs')

#configure database connections
params = config()
db = psycopg2.connect(**params)
dbcursor = db.cursor()
dbcursor.execute('SELECT version()')
db_version = dbcursor.fetchone()
logging.info("DB version", db_version)
# function definition (json,dpid,action,
def crud(d, dpid, action, i, *FileName):

    query_exec_nr = 0

    random_num = random.randrange(10000, 100000, 3)

    if action == "reg_single" or action == "reg_multiple":
        dpid = d["SourceSiteName"] + '-' + str(random_num) + '-' + date.today().isoformat()

    updatetime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
    createdtime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())

    db_query1 = "INSERT INTO dataset(Dataset_pid, DatasetName, SourceSiteName, Protocol, Hostname, Port, FilePath, CreatorName, CreatorEmail, Version, Status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    db_query2 = "UPDATE dataset set Status=%s where Dataset_pid=%s"

    db_query3 = "Insert INTO file(Dataset_pid, FileName, UpdatedTime, version, deleted) Values (%s,%s,%s,%s,0)"

    db_query4 = "UPDATE dataset set Status=%s, UpdatedTime=%s where Dataset_pid=%s"

    db_query5 = "select Dataset_pid, DatasetName, FilePath, SourceSiteName, Status, Version from dataset where Dataset_pid=%s"

    db_query6 = "select dataset_pid, filename from file where Dataset_pid=%s"

    db_query6_1 = "select dataset_pid, filename, version from file where Dataset_pid=%s and version between 0 and %s and deleted not between 1 and %s"

    db_query6_2 = "select dataset_pid, filename from file where Dataset_pid=%s"

    # files are deleted only for current working version and are indexed back in next version
    db_query6_3 = "select dataset_pid, filename from file where Dataset_pid=%s and deleted = %s"

    db_query6_4 = "select filename, gridftp_time from file where Dataset_pid=%s"

    db_query7 = "select Dataset_pid, FilePath, Hostname from dataset where Dataset_pid=%s"

    db_query8 = "select dataset_pid, filename, count(Filename) from file where Dataset_pid=%s"

    db_query9 = "select File_id from file where Dataset_pid=%s and filename=%s"

    db_query10 = "select Status, Version from dataset where Dataset_pid=%s"

    db_query11 = "update file set deleted=%s where File_id =%s and deleted=0"

    db_query12 = "UPDATE file set filechecksum=%s, updatedtime=%s where filename=%s"

    db_query13 = "UPDATE file set filebits=%s, updatedtime=%s where filename=%s"

    db_query14 = "UPDATE dataset set Status=%s, Version=%s, UpdatedTime=%s where Dataset_pid=%s"

    db_query15 = "UPDATE file set version=%s where dataset_pid=%s and version is NULL"

    db_query16 = "Select filechecksum from file where Dataset_pid=%s and filename=%s"

    db_query17 = "select filename from file where dataset_pid=%s and version between %s and %s and version NOTNULL;"

    db_query18 = "INSERT INTO subscriber(fullname, email, organisation, hostname, port, filepath, username, status, createdtime) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    db_query19 = "Select username from subscriber"

    db_query19_1 = "select username from subscriber where email=%s"

    db_query19_2 = "Select username from subscriber where username=%s"

    db_query20 = "Select dataset_id from dataset where dataset_pid=%s"

    db_query21 = "UPDATE subscriber set status=%s, updatedtime=%s where username=%s"

    db_query22 = "Select status from subscriber where username=%s"

    db_query26 = "UPDATE file set gridftp_time=%s, updatedtime=%s where filename=%s"

    db_query23 = "insert into sessions (access_token, subscriber_id, timestamp) values (%s, (select subscriber_id from subscriber where username = %s), %s)"

    db_query24 = "select subscriber_id from subscriber where email=%s"

    db_query25 = "select fullname from subscriber where subscriber_id=(select subscriber_id from sessions where access_token=%s and timestamp > current_timestamp - interval '8 hours')"

    db_query27 = "select subscriber_id from sessions where access_token=%s"

    db_query28 = "select owner_id from dataset where dataset_pid=%s" 

    db_query29 = "update dataset set owner_id=%s where dataset_pid=%s"

    db_query30 = "select port from subscriber where username=%s"

    if action == "reg_single":
        query_exec_nr = 1
        db_query = db_query1

        db_data = (dpid, d["DatasetName"], d["SourceSiteName"], d["Protocol"], d["Hostname"], d["Port"], d["FilePath"], d["CreatorName"], d["CreatorEmail"], "0", "Registered")

    elif action == "reg_multiple":
        query_exec_nr = 1
        db_query = db_query1
        db_data = (dpid, d["Source"][i]["DatasetName"], d["SourceSiteName"], d["Source"][i]["Protocol"], d["Source"][i]["Hostname"], d["Source"][i]["Port"], d["Source"][i]["FilePath"], d["Source"][i]["CreatorName"], d["Source"][i]["CreatorEmail"], "0", "Registered")

    elif action == "unreg":
        query_exec_nr = 1
        db_query = db_query2
        db_data = ("Unregistered", dpid)

    elif action == "add_file":
        query_exec_nr = 2
        db_query = db_query3
        db_data = (dpid, FileName[0], updatetime, 1) #hardoced version to 1 since the same query is used by index_add_files
        db_query_1 = db_query4
        db_data_1 = ("Open", updatetime, dpid)

    elif action == "add_files":
        query_exec_nr = 2
        db_query = db_query3
        db_data = (dpid, i, updatetime, 1) #hardoced version to 1 since the same query is used by index_add_files
        db_query_1 = db_query4
        db_data_1 = ("Open", updatetime, dpid)

    elif action == "add_file_multi_ds":
        query_exec_nr = 2
        db_query = db_query3
        db_data = (i, Filename, updatetime, 1) #hardoced version to 1 since the same query is used by index_add_files
        db_query_1 = db_query4
        db_data_1 = ("Open", updatetime, i)

    elif action == "list_dataset":
        db_query = db_query6_1 
        db_data = (dpid, d, d)
        query_exec_nr = 1

    elif action == "list_dataset_no_version":
        db_query = db_query6_2
        db_data = (dpid,)
        query_exec_nr = 1

    elif action == "get_deleted_files":
        db_query = db_query6_3
        db_data = (dpid, d)
        query_exec_nr = 1

    elif action == "index_add_files":
        query_exec_nr = 2
        db_query = db_query3
        db_data = (dpid, FileName, updatetime, d)
        db_query_1 = db_query4
        db_data_1 = ("Open", updatetime, dpid)

    elif action == "file_id":
        sqlread = db_query9

    elif action == "file_info":
        sqlread = db_query6

    elif action == "file_info_DBfile_check":
        sqlread = db_query6_4

    elif action == "file_location":
        sqlread = db_query7

    elif action == "dataset_status":
        sqlread = db_query10

    elif action == "delete_file":
        sqlread = db_query11

    elif action == "update_checksum":
        sqlread = db_query12

    elif action == "update_filesize":
        sqlread = db_query13

    elif action == "update_gridftp_timestamp":
        sqlread = db_query26

    elif action == "update_release_status":
        query_exec_nr = 2
        db_query = db_query14
        db_data = ("Released", i, updatetime, dpid)
        db_query_1 = db_query15
        db_data_1 = (i, dpid)

    elif action == "file_checksum":
        sqlread = db_query16

    elif action == "diff_db_version":
        query_exec_nr = 1
        db_query = db_query17
        db_data = (dpid, d, i)

    elif action == "add_subscriber":
        query_exec_nr = 1
        db_query = db_query18
        db_data = (d["FullName"], d["Email"], d["Organisation"], d["Hostname"], d["Port"], d["FilePath"], d["Username"], "Active", createdtime)

    elif action == "list_subscriber":
        sqlread = db_query19

    elif action == "list_user":
        query_exec_nr = 1
        db_query = db_query19_1
        db_data = (d,)

    elif action == "subscribe_user":
        query_exec_nr = 1
        db_query = db_query20
        db_data = (dpid,)

    elif action == "unsubscribe_user":
        query_exec_nr = 1
        db_query = db_query20
        db_data = (dpid,)

    elif action == "delete_subscriber":
        query_exec_nr = 1
        db_query = db_query21
        db_data = ("Inactive", updatetime, i)

    elif action == "subscriber_status":
        sqlread = db_query22

    elif action == "activate_subscriber":
        sqlread = db_query21

    elif action == "create_session":
        query_exec_nr = 1
        db_query = db_query23_1
        db_data = (d, dpid, datetime.now())

    elif action == "subscriber_id_from_email":
        query_exec_nr = 1
        db_query = db_query24
        db_data = (d,)

    elif action == "get_session":
        query_exec_nr = 1
        db_query = db_query25
        db_data = (d,)

    elif action == "get_current_user":
        query_exec_nr = 1
        db_query = db_query27
        db_data = (d,)

    elif action == "get_dataset_owner":
        query_exec_nr = 1
        db_query = db_query28
        db_data = (d,)

    elif action == "update_dataset_owner":
        query_exec_nr = 1
        db_query = db_query29
        db_data = (dpid, d)

    elif action == "datasetpid_existence":
        sqlread = db_query20

    elif action == "username_existence":
        sqlread = db_query19_2

    elif action == "transfer_port_choice":
        sqlread = db_query30

    try:
        if query_exec_nr == 1:
            dbcursor.execute(db_query, db_data)
        elif query_exec_nr == 2:
            dbcursor.execute(db_query, db_data)
            dbcursor.execute(db_query_1, db_data_1)

        db.commit()

        if not "sqlread" in locals():    #sqlread start
            if action == "list_user":
                rows = dbcursor.fetchall()
                return rows

            if action == "index_add_files":
                sqlread = "select count(FileName) from file where Dataset_pid=%s;"
                sqldata = (dpid,)
                dbcursor.execute(sqlread, sqldata)
                collect_file = dbcursor.fetchall()

                for file_num in collect_file:
                    file_collect = file_num[0]

                sqlread_1 = "select FileName from file where Dataset_pid=%s;"
                sqldata_1 = (dpid,)
                dbcursor.execute(sqlread_1, sqldata_1)
                rows = dbcursor.fetchall()
                for row in rows:
                    # instantiate a list for output
                    reply = []
                    line1 = ("Checked FilePath :", FileName)
                    line2 = ("Dataset_PID :", dpid)
                    line3 = ("Status :", "Open",)
                    line4 = ("File Num", file_collect)
                    list = [line1, line2, line3, line4]
                    for result in list:
                        reply.append(map(str, result))
                    print(reply)
                    return(reply)

            elif action == "create_session":
                # dummy branch because of lead out to connection close
                logging.info('session created')
                return "have to return othervize the db connection gets closed!"

            elif action == "subscriber_id_from_email":
                # dummy branch because of lead out to connection close
                user_id = dbcursor.fetchall()
                return user_id

            elif action == "get_session":
                session_token = dbcursor.fetchall()
                return session_token

            elif action == "get_current_user":
                current_user_id = dbcursor.fetchall()
                return current_user_id

            elif action == "get_dataset_owner":
                dataset_owner_id = dbcursor.fetchall()
                return dataset_owner_id

            elif action == "update_dataset_owner":
                logging.info('dataset owner updated')
                return "conform to rules or die"

            elif action == "update_release_status":
                sqlread = "select count(fileName), sum(filebits::bigint) from file where dataset_pid=%s;"
                sqldata = (dpid,)
                dbcursor.execute(sqlread, sqldata)
                collect_file = dbcursor.fetchall()

                for file_num in collect_file:
                    file_collect = file_num[0]
                    file_size = file_num[1]

                sqlread_1 = "select Dataset_pid, DatasetName from dataset where Dataset_pid=%s;"
                sqldata_1 = (dpid,)
                dbcursor.execute(sqlread_1, sqldata_1)
                update_status = dbcursor.fetchall()

                for name in update_status:
                    reply = []
                    datasetname = name[1]

                    line1 = ("Release version is :", i)
                    line2 = ("Datasetname : ", name[1])
                    line3 = ("DatasetPID: ", dpid)
                    line4 = ("Containing files :", str(file_collect))
                    line5 = ("Total file size (bits) :", str(file_size))
                    line6 = ("Updated time :", updatetime)
                    list = [line1, line2, line3, line4, line5, line6]
                    for result in list:
                        reply.append(map(str, result))
                    return(reply)

            elif action == "diff_db_version":
                sqlread = "select dataset_pid, filename from file where dataset_pid=%s and version between %s and %s and version NOTNULL"
                sqldata = (dpid, d, i)
                dbcursor.execute(sqlread, sqldata)
                rows = dbcursor.fetchall()
                reply = []
                for row in rows:
#                    print "%s", (row[1])
                    reply.append(row[1])
                logging.info('this is a reply from diff_db_version from db_manage:')
                return(reply)

            elif action == "get_subs":
                sqlread = "select fullname, dataset_pid, email, username from subscription inner join subscriber on subscriber.subscriber_id = subscription.subscriber_id inner join dataset on dataset.dataset_id = subscription.dataset_id"
                dbcursor.execute(sqlread,)
                rows = dbcursor.fetchall()
                logging.info(rows)
                logging.info('this is print reply from get_subs(db_manage)')
                logging.info('this happens between print(reply) and return(reply) in get_subs()')
                return(rows)

            elif action == "get_subs_host":
                sqlread = "select dataset_id from dataset where dataset_pid=%s;"
                sqldata = (dpid,)
                dbcursor.execute(sqlread, sqldata)
                rows = dbcursor.fetchall()

                for n in rows:
                    data_id = n[0]
                sqlread_1 = "select subscriber_id from subscription where dataset_id=%s;"
                sqldata_1 = (data_id,)
                dbcursor.execute(sqlread_1, sqldata_1)
                list = dbcursor.fetchall()

                for sub in list:
                    sub_id = list[0]

                sqlread_2 = "select hostname, filepath from subscriber where subscriber_id=%s;"
                sqldata_2 = (sub_id,)
                dbcursor.execute(sqlread_2, sqldata_2)
                hostlist = dbcursor.fetchall()
                return(hostlist)

            elif action == "get_one_sub_host":
                sqlread = "select hostname, filepath from subscriber where username=%s;"
                sqldata = (i,)
                dbcursor.execute(sqlread, sqldata)
                hostlist = dbcursor.fetchall()
                return(hostlist)

            elif action == "get_one_sub_email":
                sqlread = "select email from subscriber where username=%s;"
                sqldata = (i,)
                dbcursor.execute(sqlread, sqldata)
                email_info = dbcursor.fetchall()
                return(email_info)

            elif action == "add_subscriber":
                sqlread = "select fullname, email, organisation from subscriber where username=%s;"
                sqldata = (i,)
                dbcursor.execute(sqlread, sqldata)
                subscriber_list = dbcursor.fetchall()

                for name in subscriber_list:
                    fullname = name[0]
                    email = name[1]
                    organisation = name[2]

                    reply = []
                    line1 = ("Fullname :", fullname)
                    line2 = ("Email :", email)
                    line3 = ("Organisation :", organisation)
                    line4 = ("Username :", i)
                    list = [line1, line2, line3, line4]
                    for result in list:
                        reply.append(map(str, result))
                    return(reply)

            elif action == "get_dataset_last_version":
                sqlread = "select version from dataset where dataset_pid=%s"
                sqldata = (dpid,)
                dbcursor.execute(sqlread, sqldata)
                rows = dbcursor.fetchall()
                return(rows)

            elif action == "get_file_last_version":
                sqlread = "select MAX(version) from file where dataset_pid=%s and filename=%s"
                sqldata = (dpid, i)
                dbcursor.execute(sqlread, sqldata)
                rows = dbcursor.fetchall()
                return(rows)

            elif action == "list_dataset" or action == "list_dataset_no_version":
                rows = dbcursor.fetchall() 
                reply = []
                for row in rows:
                    reply.append(row[1])
                return(reply)

            elif action == "get_deleted_files":
                rows = dbcursor.fetchall()
                reply = []
                for row in rows:
                    reply.append(row[1])
                return(reply)

            elif action == "subscribe_user":
                rows = dbcursor.fetchall()
                for row in rows:
                    datasetid = row[0]
                sqlread = "Select subscriber_id from subscriber where username=%s;"
                sqldata = (i,)
                dbcursor.execute(sqlread, sqldata)
                sub_ids = dbcursor.fetchall()
                for id in sub_ids:
                    sub_id = id[0]

                # check if there is the same data in DB
                sqlread_1 = "Select subscriber_id, dataset_id from subscription where subscriber_id=%s and dataset_id=%s;"
                sqldata_1 = (sub_id, datasetid)
                dbcursor.execute(sqlread_1, sqldata_1)
                db_result = dbcursor.fetchall()

                if db_result:
                    sqlread_2 = "UPDATE subscription set status=%s, updatedtime=%s where subscriber_id=%s"
                    sqldata_2 = ("Active", updatetime, sub_id)
                    dbcursor.execute(sqlread_2, sqldata_2)
                    db.commit()
                    return True

                else:
                    # No the same data in DB and will add it
                    sqlread_3 = "INSERT INTO subscription(subscriber_id, dataset_id,status,createdtime) VALUES (%s,%s,%s,%s);"
                    sqldata_3 = (sub_id, datasetid, "Active", createdtime)
                    reply = dbcursor.execute(sqlread_3, sqldata_3)
                    db.commit()
                    return True

            elif action == "unsubscribe_user":
                rows = dbcursor.fetchall()
                for row in rows:
                    datasetid = row[0]
                sqlread = "Select subscriber_id from subscriber where username=%s;"
                sqldata = (i,)
                dbcursor.execute(sqlread, sqldata)
                sub_ids = dbcursor.fetchall()
                for id in sub_ids:
                    sub_id = id[0]

                # check if there is data in DB
                try:
                    sqlread_1 = "Select subscriber_id, dataset_id from subscription where subscriber_id=%s and dataset_id=%s;"
                    sqldata_1 = (sub_id, datasetid)
                    dbcursor.execute(sqlread_1, sqldata_1)
                    db_result = dbcursor.fetchall()

                    if db_result:
                        #There is a data in DB, delete it and set this subscriber is inactive
                        sqlread_2 = "UPDATE subscription set status=%s, updatedtime=%s where subscriber_id=%s and dataset_id=%s;"
                        sqldata_2 = ("Inactive", updatetime, sub_id, datasetid)
                        dbcursor.execute(sqlread_2, sqldata_2)
                        db.commit()
                        return True

                    else:
                        logging.warning('No this username and datasetid in DB')
                        return False

                except:
                    logging.error('there is a problem to search this username and datasetid')

            elif action == "delete_subscriber":
                #will set subscriber status as Inactive and all subscribed datasets changes to Inactive!!
                sqlread = "Select subscriber_id from subscriber where username=%s;"
                sqldata = (i,)
                dbcursor.execute(sqlread, sqldata)
                sub_ids = dbcursor.fetchall()
                for id in sub_ids:
                    sub_id = id[0]
                    # Update all dataset status with this subscriber_id
                    sqlread_2 = "UPDATE subscription set status=%s, updatedtime=%s where subscriber_id=%s"
                    sqldata_2 = ("Inactive", updatetime, sub_id)
                    dbcursor.execute(sqlread_2, sqldata_2)
                    db.commit()

            elif action == "sub_list":
                sqlread = "select dataset_pid from subscription inner join subscriber on subscriber.subscriber_id = subscription.subscriber_id inner join dataset on dataset.dataset_id = subscription.dataset_id where username=%s and subscription.status=%s;"
                sqldata = (i, "Active")
                dbcursor.execute(sqlread, sqldata)
                rows = dbcursor.fetchall()
                reply = []
                for row in rows:
                    reply.append(row[0])
                return(reply)

            elif action == "sub_list_detail":
                sqlread = "select hostname from subscriber where username=%s;"
                sqldata = (i,)
                dbcursor.execute(sqlread, sqldata)
                hostname = dbcursor.fetchall()
                for info in hostname:
                    host = info[0]

                sqlread_1 = "select Dataset_pid, Status, Version from dataset where Dataset_pid=%s"
                sqldata_1 = (dpid,)
                dbcursor.execute(sqlread_1, sqldata_1)
                rows = dbcursor.fetchall()

                for row in rows:
                    reply = []
                    line1 = ("Dataset_pid", row[0])
                    line2 = ("Status", row[1])
                    line3 = ("Released Version", row[2],)
                    line4 = ("Target Host", host,)
                    list = [line1, line2, line3, line4]
                    for i in list:
                        reply.append(map(str, i))
                    return(reply)

            else:#elif action=="list_dataset"i used by register
                sqlread = "select Dataset_pid, DatasetName, Status from dataset where Dataset_pid=%s;"
                sqldata = (dpid,)
                dbcursor.execute(sqlread, sqldata)
                rows = dbcursor.fetchall()
                print "list DS"
                for row in rows:
                    reply = []
                    line1 = ("Dataset_PID :", row[0])
                    line2 = ("DataName :", row[1])
                    line3 = ("Status :", row[2],)
                    list = [line1, line2, line3]
                    for i in list:
                        reply.append(map(str, i))
                    return(reply)

        else:
            if action == "file_info":
                sqldata = (dpid,)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "file_location":
                sqldata = (dpid,)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "file_id":
                sqldata = (dpid, i)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "dataset_status":
                sqldata = (dpid,)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "delete_file":
                sqldata = (d, i)
                sqlquery = sqlread
                rows = dbcursor.execute(sqlquery, sqldata)
                db.commit()
                return

            elif action == "update_checksum":
                # Checksum is first one(dpid), filepath is the last one(i)
                sqldata = (dpid, updatetime, i)
                sqlquery = sqlread
                rows = dbcursor.execute(sqlquery, sqldata)
                db.commit()
                return

            elif action == "update_filesize":
                # filesize is first one(dpid), filepath is the last one(i)
                sqldata = (dpid, updatetime, i)
                sqlquery = sqlread
                rows = dbcursor.execute(sqlquery, sqldata)
                db.commit()
                return

            elif action == "update_gridftp_timestamp":
                # gridftp_timestamp is first one(dpid), filepath is the last one(i)
                sqldata = (dpid, updatetime, i)
                sqlquery = sqlread
                rows = dbcursor.execute(sqlquery, sqldata)
                db.commit()
                return

            elif action == "file_info_DBfile_check":
                sqldata = (dpid,)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "file_checksum":
                sqldata = (dpid, i)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "list_subscriber":
                sqldata = ('')
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "subscriber_status":
                sqldata = (i,)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "activate_subscriber":
                sqldata = ("Active", updatetime, i)
                sqlquery = sqlread
                rows = dbcursor.execute(sqlquery, sqldata)
                db.commit()
                return True

            elif action == "datasetpid_existence":
                sqldata = (dpid,)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "username_existence":
                sqldata = (i,)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            elif action == "transfer_port_choice":
                sqldata = (d,)
                sqlquery = sqlread
                return db_raw(sqlquery, sqldata)

            else:
                sqldata = (dpid,)
                dbcursor.execute(sqlread, sqldata)
                rows = dbcursor.fetchall()
                reply = []
                for row in rows:
                    reply.append(row[1])
                return(reply)

    except psycopg2.Error as e:
        # parametrise this message
        logging.error('We have a problem with dataset operation!')
        logging.error(e.pgerror)
        logging.error(e.diag.message_detail)
        db.rollback()
        db.reset()
    db.close()
#    print "came until db.close"

def db_raw(sqlquery, sqldata):
    dbcursor.execute(sqlquery, sqldata)
    rows = dbcursor.fetchall()
    logging.info(rows)
    return rows

    #db.close() Needs checking whether this one is needed at all. Check psycopg2 standard workflow!!!
    #print "last db.close"
