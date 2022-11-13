from flask import Flask, json, jsonify, request, session
from flask_cors import CORS
import pymongo
from bson.objectid import ObjectId
import random
import string

import config

from werkzeug.utils import redirect

app = Flask(__name__)
CORS(app)
app.secret_key = '2abceVR5ENE7FgMxXdMwuzUJKC2g8xgy'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

app.config['mongo_connection'] = pymongo.MongoClient(config.mongo_url)['haunting']

@app.route('/v1/generate_game', methods=['GET'])
def generateGame():
    tiles_col = app.config['mongo_connection']['tiles']
    join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    tiles = []
    for tile in tiles_col.find():
        tiles.append(tile)
    session = {
        'join_code':join_code,
        'available_tiles':tiles,
        'players':[],
        'tiles':[],
        'status':'started'
    }

    game_sessions_col = app.config['mongo_connection']['sessions']
    game_sessions_col.insert_one(session)
    return jsonify({'message':'success', 'join_code':join_code})

@app.route('/v1/game', methods=['GET', 'POST', 'PUT'])
def updateGame():
    if request.method == 'GET':
        game_sessions_col = app.config['mongo_connection']['sessions']
        search_query = {
            'join_code':request.args.get('join_code')
        }
        session = game_sessions_col.find_one(search_query)
        return jsonify(convertToJSON(session))

    elif request.method == 'POST':
        game_sessions_col = app.config['mongo_connection']['sessions']
        search_query = {
            'join_code':request.json['join_code']
        }
        session = game_sessions_col.find_one(search_query)
        print(request.json)
        
        update_query = {
            "$push":{
                "players":{
                    "col":12,
                    "floor":"ground",
                    "row":13,
                    "display_name":request.json['display_name']
                }
            }
        }

        game_sessions_col.update_one(search_query, update_query)

        return jsonify(convertToJSON(session))

    elif request.method == 'PUT':
        game_sessions_col = app.config['mongo_connection']['sessions']
        search_query = {
            'join_code':request.json['join_code']
        }
        update_query = {
            '$set':{
            }
        }
        try:
            if request.json['available_tiles']:
                update_query['$set']['available_tiles'] = request.json['available_tiles']
        except:
            print('No Available Tiles Update')
          
        try:  
            if request.json['tiles']:
                update_query['$set']['tiles'] = request.json['tiles']
        except:
            print('No Tiles Update')

        game_sessions_col.update_one(search_query, update_query)
        return jsonify({'message':'success'})

@app.route('/v1/leave_game', methods=['POST'])
def leaveGame():
    if request.method == 'POST':
        game_sessions_col = app.config['mongo_connection']['sessions']
        search_query = {
            'join_code':request.json['join_code']
        }
        session = game_sessions_col.find_one(search_query)

        curr_players = session['players']
        new_players = []
        try:
            for player in curr_players:
                if player['display_name'] != request.json['display_name']:
                    new_players.append(player)
        except:
            pass
        
        update_query = {
            "$set":{
                "players":new_players
            }
        }

        game_sessions_col.update_one(search_query, update_query)

        return jsonify(convertToJSON(session))

def convertToJSON(obj):
    objData = {}
    for key in obj:
        if key != 'password':
            if isinstance(obj[key], list):
                objData[key] = []
                thisList = []
                for x in range(0, len(obj[key])):
                    if isinstance(obj[key][x], str):
                        objData[key].append(str(obj[key][x]))
                    elif isinstance(obj[key][x], bytes):
                        objData[key].append(str(obj[key][x]))
                    elif isinstance(obj[key][x], bool):
                        objData[key].append((obj[key][x]))
                    elif isinstance(obj[key][x], int):
                        objData[key] = int(obj[key][x])
                    elif isinstance(obj[key][x], float):
                        objData[key] = float(obj[key][x])
                    elif isinstance(obj[key][x], ObjectId):
                        objData[key].append(str(obj[key][x]))
                    else:
                        thisDict = {}
                        for listKey in obj[key][x]:
                            if isinstance(listKey, dict):
                                if isinstance(thisDict, dict):
                                    thisDict = []
                                thisDict.append(listKey)
                            else:
                                if isinstance(obj[key][x][listKey], str):
                                    thisDict[listKey] = str(obj[key][x][listKey])
                                elif isinstance(obj[key][x][listKey], bytes):
                                    thisDict[listKey] = str(obj[key][x][listKey])
                                elif isinstance(obj[key][x][listKey], bool):
                                    thisDict[listKey] = obj[key][x][listKey]
                                elif isinstance(obj[key][x][listKey], int):
                                    thisDict[listKey] = int(obj[key][x][listKey])
                                elif isinstance(obj[key][x][listKey], float):
                                    thisDict[listKey] = float(obj[key][x][listKey])
                                elif isinstance(obj[key][x][listKey], ObjectId):
                                    thisDict[listKey] = str(obj[key][x][listKey])
                                else:
                                    thisDict[listKey] = obj[key][x][listKey]
                        thisList.append(thisDict)
                
                        objData[key] = thisList

            else:
                if isinstance(obj[key], str):
                    objData[key] = str(obj[key])
                elif isinstance(obj[key], bytes):
                    objData[key] = str(obj[key])
                elif isinstance(obj[key], bool):
                    objData[key] = obj[key]
                elif isinstance(obj[key], int):
                    objData[key] = int(obj[key])
                elif isinstance(obj[key], float):
                    objData[key] = float(obj[key])
                elif isinstance(obj[key], ObjectId):
                    objData[key] = str(obj[key])
                else:
                    objData[key] = obj[key]
    try:
        objData['id'] = objData['_id']
        objData.pop('_id')
    except:
        pass
    return objData

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)