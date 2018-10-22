#!/usr/bin/python

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

class EMAIL_METHOD():

    def start_transfer_email(self, dpid, diff_list, subscriber_email):
        email_body = []
        email_body.append(dpid)
        for element in diff_list:
            email_body.append(element)
        sum = len(diff_list)
        email_body.append("Total files will be transferred: %s" % sum)
        email_body_str = "\n".join(email_body)
        self.send_email(subscriber_email, email_body_str)
        return True

    def success_content(self, dpid, diff_list, subscriber_email):
        email_body = []
        email_body.append(dpid)
        for element in diff_list:
            email_body.append(element)
        email_body.append("File Transfer is done")
        email_body.append("Total files are already transferred: %s" % len(diff_list))
        email_body_str = "\n".join(email_body)
        self.send_transfer_result(subscriber_email, email_body_str)
        return True

    def fail_content(self, dpid, diff_list, subscriber_email):
        email_body = []
        email_body.append(dpid)
        for element in diff_list:
            email_body.append(element)
        email_body.append("[ERROR] File Transfer is failed, please check it!!!")
        email_body_str = "\n".join(email_body)
        self.send_transfer_error(subscriber_email, email_body_str)
        return False

    def fail_fts_content(self, dpid, diff_list, subscriber_email, result, all_info):
        email_body = []
        email_body.append(dpid)
        for element in diff_list:
            email_body.append(element)
        email_body.append("[ERROR] File Transfer is failed, please check it!!!")
        email_body.append("FINISHED ITEMS ARE: %s" % result.count("FINISHED"))
        email_body.append("SUBMITTED ITEMS ARE: %s" % result.count("SUBMITTED"))
        email_body.append("FAILED ITEMS ARE: %s" % result.count("FAILED"))
        email_body.append("Details: %s" % all_info)
        email_body_str = "\n".join(email_body)
        self.send_transfer_error(subscriber_email, email_body_str)
        return False

    def fail_fts_delegation(self, dpid, diff_list, subscriber_email):
        email_body = []
        email_body.append(dpid)
        for element in diff_list:
            email_body.append(element)
        email_body.append("[ERROR] Something wrong on FTS delegation.")
        email_body_str = "\n".join(email_body)
        self.send_transfer_error(subscriber_email, email_body_str)
        return False

    def success_fts_delegation(self, dpid, diff_list, subscriber_email):
        email_body = []
        email_body.append(dpid)
        for element in diff_list:
            email_body.append(element)
        email_body.append("FTS delegation Correct!!")
        email_body_str = "\n".join(email_body)
        self.send_transfer_result(subscriber_email, email_body_str)
        return True

    def send_email(self, subscriber, transfer_list):
        smtp = smtplib.SMTP()
        smtp.connect('localhost')
        msgRoot = MIMEMultipart("alternative")
        msgRoot['Subject'] = Header("DSDS Dataset Subscription Service", "utf-8")
        msgRoot['From'] = "service@dsds-service.ebi.ac.uk"
        msgRoot['To'] = subscriber
        text = MIMEText(transfer_list, "plain", "utf-8")
        msgRoot.attach(text)
        smtp.sendmail("service@dsds-service.ebi.ac.uk", [subscriber], msgRoot.as_string())

    def send_transfer_result(self, subscriber, transfer_list):
        smtp = smtplib.SMTP()
        smtp.connect('localhost')
        msgRoot = MIMEMultipart("alternative")
        msgRoot['Subject'] = Header("DSDS Dataset Subscription Service Transfer is Done", "utf-8")
        msgRoot['From'] = "service@dsds-service.ebi.ac.uk"
        msgRoot['To'] = subscriber
        text = MIMEText(transfer_list, "plain", "utf-8")
        msgRoot.attach(text)
        smtp.sendmail("service@dsds-service.ebi.ac.uk", [subscriber], msgRoot.as_string())

    def send_transfer_error(self, subscriber, transfer_list):
        smtp = smtplib.SMTP()
        smtp.connect('localhost')
        msgRoot = MIMEMultipart("alternative")
        msgRoot['Subject'] = Header("DSDS Dataset Subscription Service Transfer is failed", "utf-8")
        msgRoot['From'] = "service@dsds-service.ebi.ac.uk"
        msgRoot['To'] = subscriber
        msgRoot['To'] = "rdsds@ebi.ac.uk"
        text = MIMEText(transfer_list, "plain", "utf-8")
        msgRoot.attach(text)
        smtp.sendmail("service@dsds-service.ebi.ac.uk", [subscriber], msgRoot.as_string())
        smtp.sendmail("service@dsds-service.ebi.ac.uk", "rdsds@ebi.ac.uk", msgRoot.as_string())

