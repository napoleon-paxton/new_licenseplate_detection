import json
from flask import Flask, jsonify, request
from videoTextDetection import TextDetection

app=Flask(__name__)

@app.route('/myapp/detectText', defaults={'name': 'accident_scene.mp4'})

@app.route('/myapp/detectText/<name>')
def Textdetect(name):
    #img=request.args['bezos_vogel.mp4']
    #img_path = './'+img
    results=TextDetection(name)
    return jsonify({'TextDetected':results})

app.run(host="0.0.0.0", port="5000")
