import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request, jsonify
import pymongo
from pymongo import cursor
from pymongo.synchronous.database import Database

from typing import Mapping, Any


app = Flask(__name__)


client: pymongo.MongoClient[Mapping[str, Any]]
database: Database[Mapping[str, Any]]
json_map: dict[str, Any]

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


try:
    # Creating a MongoClient to connect to the local MongoDB server
    client = pymongo.MongoClient(
        os.getenv("MONGODB_CONNECTION_STRING"),
        tls=True,
        tlsAllowInvalidCertificates=True
    )

    database = client[os.getenv("DATABASE_NAME")]


except Exception as e:
    # Handling exceptions and printing an error message if collection creation fails
    print(f"Error: {e}")


def get_list_of(collection):
    my_list = collection.find()

    my_json = []

    for item in my_list:
        # Convert ObjectId to string
        item['_id'] = str(item['_id'])
        my_json.append(item)

    return jsonify(my_json), 200


def get_item(collection, identifier: str):
    my_query = {"_id": identifier}
    my_item = collection.find(my_query)

    my_json = []

    for item in my_item:
        # Convert ObjectId to string
        item['_id'] = str(item['_id'])
        my_json.append(item)

    return jsonify(my_json), 200


def bad_response(error):
    response_body = {
        "response": "Bad request",
        "error": error
    }
    return jsonify(response_body), 400


def conflict(error):
    response_body = {
        "response": "Conflict",
        "error": error
    }
    return jsonify(response_body), 409


def success(code):
    response_body = {
        "response": "success"
    }
    return jsonify(response_body), code


def get_last_id(collection):
    my_list = collection.find().sort("_id", -1)

    try:
        record = cursor.next(my_list)
        return record['_id']
    except StopIteration:
        return bad_response("Empty list")


@app.route("/get-users")
def get_users():
    users_collection = database["users"]

    return get_list_of(users_collection)


# Sample users: 1001, 1002, 1003
@app.route("/get-user/<desired_id>")
def get_user_by_id(desired_id):
    users_collection = database["users"]

    return get_item(users_collection, desired_id)


@app.route("/get-conversations")
def get_conversations():
    conversations_collection = database["conversations"]

    return get_list_of(conversations_collection)


@app.route("/get-conversation/<desired_id>")
def get_conversation_by_id(desired_id):
    conversations_collection = database["conversations"]

    return get_item(conversations_collection, desired_id)


@app.route("/create-conversation/<user_id>", methods=["POST"])
def create_conversation(user_id):
    try:
        conversations_collection = database["conversations"]

        my_query = {"_id": user_id}
        item_count = conversations_collection.count_documents(my_query)

        if item_count != 0:
            return conflict("Record exists")

        # Creating a dictionary with student details
        data = {
            '_id': user_id,
            'textrecords': []
        }

        conversations_collection.insert_one(data)

        return success(201)

    except Exception as error:
        # Handling exceptions and printing an error message if data insertion fails
        print(f"Error: {error}")
        return bad_response(error)


@app.route("/create-user", methods=["POST"])
def create_user():
    try:
        params = request.args

        users_collection = database["users"]
        index = get_last_id(users_collection)
        new_index = str(int(index) + 1)

        if not params.get("email") or not params.get("name"):
            return bad_response("Missing parameter")

        # Creating a dictionary with student details
        data = {
            '_id': new_index,
            'email': params.get("email"),
            'name': params.get("name")
        }

        # Inserting the student data into the 'students' collection
        users_collection.insert_one(data)

        # Printing a message indicating the successful insertion of data with the obtained ID
        return success(201)

    except Exception as error:
        # Handling exceptions and printing an error message if data insertion fails
        print(f"Error: {error}")
        return bad_response(error)


@app.route("/create-doc", methods=["POST"])
def create_doc():
    try:
        params = request.args

        document_collection = database["document"]
        index = get_last_id(document_collection)
        new_doc_index = str(int(index) + 1)

        if not params.get("docname"):
            return bad_response("Missing parameter docname")

        # Creating a dictionary with student details
        data = {
            '_id': new_doc_index,
            'docname': params.get("docname")
        }

        # Inserting the student data into the 'students' collection
        document_collection.insert_one(data)

        # Printing a message indicating the successful insertion of data with the obtained ID
        return success(201)

    except Exception as error:
        # Handling exceptions and printing an error message if data insertion fails
        print(f"Error: {error}")
        return bad_response(error)


@app.route("/update-conversation/<user_id>", methods=["PUT"])
def update_conversation(user_id):
    try:
        conversations_collection = database["conversations"]
        id_query = {"_id": user_id}
        convo = conversations_collection.find_one(id_query)
        record_to_update: list = convo["textrecords"]

        record_data = {
            "timestamp": "",
            "record": [
                {
                    "user": "Howdy!",
                    "ai": "Howdy, how are you?"
                },
                {
                    "user": "Perfect",
                    "ai": "Glad to hear that. How can I help you today?"
                }
            ]
        }

        record_data = request.get_json()

        record_to_update.append(record_data)

        new_value = {
            "textrecords": record_to_update
        }

        conversations_collection.update_one({'_id': user_id}, {"$set": new_value}, upsert=False)

        return success(201)

    except Exception as error:
        # Handling exceptions and printing an error message if data insertion fails
        print(f"Error: {error}")

        return bad_response(error)


if __name__ == "__main__":
    app.run(debug=True)
