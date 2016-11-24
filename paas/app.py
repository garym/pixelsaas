#!/usr/bin/env python

from flask import Flask, abort, jsonify, make_response
from flask_restful import Api, Resource, fields, marshal, reqparse
from flask_httpauth import HTTPBasicAuth

from pixelcontrol import PixelDB

app = Flask(__name__, static_url_path="")
api = Api(app)
auth = HTTPBasicAuth()

pixelDB = PixelDB()

@auth.get_password
def get_password(username):
    if username == 'admin':
        return 'admin'
    return None


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message': 'Unauthorized access'}), 401)

base_api_path = '/paas/api'
base_api_path_v1 = base_api_path + '/v1.0'


def get_all_pixels():
    data = pixelDB.get_pixels()
    return (
        {
            'id': d['id'],
            'colour': d['colour'],
            'time': d['time'],
        } for d in data if d is not None)

def get_pixel(pixelid):
    pixel = pixelDB.get_pixel(pixelid)
    
    data = {
        'id': pixelid,
        'colour': pixel['colour'] if pixel is not None else dict(zip('rgb', (0, 0, 0))),
        'time': 0 if pixel is None else pixel['time']
    }
    return data

def set_pixel(pixelid, colour):
    pixel = pixelDB.set_pixel(pixelid, colour)
    data = {
        'id': pixelid,
        'colour': pixel['colour'] if pixel is not None else dict(zip('rgb', (0, 0, 0))),
        'time': 0 if pixel is None else pixel['time'],
    }
    return data

def delete_pixel(pixelid):
    pixel = pixelDB.delete_pixel(pixelid)
    return True

colour_fields = {
    'r': fields.Integer,
    'g': fields.Integer,
    'b': fields.Integer,
}

pixel_fields = {
    'colour': fields.Nested(colour_fields),
    'time': fields.Integer,
    'uri': fields.Url('pixel')
}


class PixelListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'colour', type=list, required=True,
            help='Missing colour for pixel', location='json')
        self.reqparse.add_argument(
            'time', type=int, default=-1, location='json')
        super(PixelListAPI, self).__init__()

    def get(self):
        return {'pixels': [marshal(p, pixel_fields) for p in get_all_pixels()]}


class PixelAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'colour', type=dict, location='json')
        self.reqparse.add_argument(
            'time', type=int, location='json')
        super(PixelAPI, self).__init__()

    def get(self, id):
        pixel = get_pixel(id)
        if pixel is None:
            abort(404)
        return {'pixel': marshal(pixel, pixel_fields)}

    def put(self, id):
        pixel = get_pixel(id)
        if pixel is None:
            abort(404)
        args = self.reqparse.parse_args()
        for k, v in args.iteritems():
            if v != None:
                pixel[k] = v
        updated_pixel = set_pixel(id, pixel['colour'])
        return {'pixel': marshal(updated_pixel, pixel_fields)}

    def delete(self, id):
        pixel = get_pixel(id)
        if pixel is None or pixel.get('time', 0) is 0:
            abort(404)
        result = delete_pixel(id)
        return {'result': result}

api.add_resource(PixelListAPI, base_api_path_v1 + '/pixels', endpoint = 'pixels')
api.add_resource(PixelAPI, base_api_path_v1 + '/pixels/<int:id>', endpoint = 'pixel')


if __name__ == '__main__':
    app.run(debug=True)

