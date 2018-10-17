from flask import Flask

app = Flask(__name__)
import dsds.dsds_rest_service
import dsds.google_oauth
import logging
from logging.handlers import RotatingFileHandler
import dsds.service_scheduler
SECRET_KEY = 'development key'
app.secret_key = SECRET_KEY
app.debug = True

dsds.service_scheduler.scheduler.start()
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

#if __name__ == '__main__':
#    app.run(debug=True,host= '0.0.0.0')
