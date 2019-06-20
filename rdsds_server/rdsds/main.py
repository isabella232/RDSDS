from flask import Flask, jsonify
from flask_swagger import swagger

app = Flask(__name__)


@app.route("/api/v1.0/doc")
def spec():
    swag = swagger(app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "Reference Data Set Distribution Service"
    swag['info']['service description'] = "This service provides and manages the technical metadata lifecycle relating to reference dataset stored in the ELIXIR data federation"
    swag['info']['service contact'] = "rdsds@ebi.ac.uk"
    swag['info']['service license'] = "Apache 2"
    return jsonify(swag)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)