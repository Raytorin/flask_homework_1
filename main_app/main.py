from typing import Type
from hashlib import md5
import json

from flask import Flask, jsonify, request
from flask.views import MethodView
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from models import Session, User, Advertisement
from schema import PostUser, PatchUser, PostAdv, PatchAdv


app = Flask('app')
app.config['JSON_AS_ASCII'] = False


def hash_password(password: str):
    password: bytes = password.encode()
    hashed_password = md5(password).hexdigest()
    return hashed_password


def validate(json_data, model_class):
    try:
        model_item = model_class(**json_data)
        return model_item.model_dump(exclude_none=True)
        # return model_item.dict(exclude_none=True)
    except ValidationError as err:
        raise HttpError(400, err.errors())


class HttpError(Exception):

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HttpError)
def error_handler(error: HttpError):
    response = jsonify({'status': 'error', 'message': error.message})
    response.status_code = error.status_code
    return response


def get_user(user_id: int, session: Session):
    user = session.get(User, user_id)
    if user is None:
        raise HttpError(404, message='user not found')

    return user


def get_adv(adv_id: int, session: Session):
    advertisement = session.get(Advertisement, adv_id)
    if advertisement is None:
        raise HttpError(404, message='advertisement not found')

    return advertisement


def authentication(request):
    email = request.headers.get('email')
    password = request.headers.get('password')
    if not email or not password:
        raise HttpError(404, message='empty email or password')
    hashed_password = hash_password(password)
    with Session() as session:
        result = session.query(User).filter(
            User.user_email == email,
            User.user_password == hashed_password
        ).first()
    if not result:
        raise HttpError(404, message='invalid authenticate')
    else:
        return result


class UserView(MethodView):

    def get(self, user_id: int):
        with Session() as session:
            user = get_user(user_id, session)
            return jsonify({
                'id': user_id,
                'username': user.user_name,
                'email': user.user_email,
                'creation_time': user.creation_time.isoformat()
            })

    def post(self):
        # json_data = request.json
        # json_data['user_name'] = json_data['user_name'].encode().decode('unicode-escape')
        json_data = validate(request.json, PostUser)
        json_data['user_password'] = hash_password(json_data['user_password'])
        with Session() as session:
            new_user = User(**json_data)
            session.add(new_user)
            try:
                session.commit()
            except IntegrityError as er:
                raise HttpError(409, 'user already exists')
            return jsonify({
                'id': new_user.id
            })

    def patch(self, user_id: int):
        # json_data = request.json
        json_data = validate(request.json, PatchUser)
        if 'user_password' in json_data:
            json_data['user_password'] = hash_password(json_data['user_password'])

        with Session() as session:
            user = get_user(user_id, session)
            for field, value in json_data.items():
                setattr(user, field, value)
            try:
                session.commit()
            except IntegrityError as er:
                raise HttpError(409, 'username is busy')

            return jsonify({
                'id': user.id,
                'username': user.user_name,
                'creation_time': int(user.creation_time.timestamp())
            })

    def delete(self, user_id: int):
        with Session() as session:
            user = get_user(user_id, session)
            session.delete(user)
            session.commit()
            return jsonify({
                'status': 'success'
            })


class AdvView(MethodView):

    def get(self, adv_id: int):
        with Session() as session:
            adv = get_adv(adv_id, session)
            return jsonify({
                'id': adv_id,
                'title': adv.title,
                'description': adv.description,
                'created_at': adv.created_at.isoformat()
            })

    def post(self):
        user_auth = authentication(request)
        json_old_data = request.json
        json_data = validate(json_old_data, PostAdv)
        json_data['owner_id'] = user_auth.id
        with Session() as session:
            new_adv = Advertisement(**json_data)
            session.add(new_adv)
            try:
                session.commit()
            except IntegrityError as er:
                raise HttpError(409, 'advertisement already exists')
            return jsonify({
                'id': new_adv.id
            })

    def patch(self, adv_id: int):
        user_auth = authentication(request)
        json_old_data = request.json
        json_data = validate(json_old_data, PatchAdv)
        json_data['owner_id'] = user_auth.id
        with Session() as session:
            result = session.query(User).join(Advertisement).filter(
                User.id == user_auth.id,
                Advertisement.id == adv_id
            ).first()
        if not result:
            raise HttpError(404, message='you cannot interact with this ad')
        with Session() as session:
            adv = get_adv(adv_id, session)
            for field, value in json_data.items():
                setattr(adv, field, value)
            try:
                session.commit()
            except IntegrityError as er:
                raise HttpError(409, 'advertisement is busy')

            return jsonify({
                'id': adv_id,
                'title': adv.title,
                'description': adv.description,
                'created_at': int(adv.created_at.timestamp())
            })

    def delete(self, adv_id: int):
        user_auth = authentication(request)
        with Session() as session:
            adv = get_adv(adv_id, session)
            session.delete(adv)
            session.commit()
            return jsonify({
                'status': 'success'
            })


app.add_url_rule('/user/<int:user_id>',
                 view_func=UserView.as_view('user_existed'),
                 methods=['GET', 'PATCH', 'DELETE', ])

app.add_url_rule('/user',
                 view_func=UserView.as_view('user_new'),
                 methods=['POST', ])

app.add_url_rule('/advertisement/<int:adv_id>',
                 view_func=AdvView.as_view('adv_existed'),
                 methods=['GET', 'PATCH', 'DELETE', ])

app.add_url_rule('/advertisement',
                 view_func=AdvView.as_view('adv_new'),
                 methods=['POST', ])


if __name__ == '__main__':
    app.run(host='127.0.0.1', post=5000)
