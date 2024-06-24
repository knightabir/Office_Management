import json
import sys
from datetime import datetime, timedelta

import tornado.web
from bson import ObjectId
from build_config import CONFIG
from util.conn_util import MongoMixin
from util.log_util import Log
from util.time_util import timeNow
from bson.json_util import dumps as bdumps
from helper.jwt_helper import JWT_DECODE_1, JWT_ENCODE_1
from helper.decorators import all_origin


class CompanyDashboardHandler(tornado.web.RequestHandler, MongoMixin):

    SUPPORTED_METHODS = ('OPTIONS', 'POST', 'PUT', 'GET')

    user = MongoMixin.userDb[
        CONFIG['database'][0]['table'][12]['name']
    ]

    company = MongoMixin.userDb[
        CONFIG['database'][0]['table'][13]['name']
    ]

    branch = MongoMixin.userDb[
        CONFIG['database'][0]['table'][14]['name']
    ]

    obBoard = MongoMixin.userDb[
        CONFIG['database'][0]['table'][15]['name']
    ]
    role = MongoMixin.userDb[
        CONFIG['database'][0]['table'][15]['name']
    ]

    project = MongoMixin.userDb[
        CONFIG['database'][0]['table'][19]['name']
    ]

    def options(self):
        response = {
            'code': 4100,
            'status': False,
            'message': '',
            'result': []
        }
        self.set_status(200)
        self.write(response)
        self.finish()

    async def get(self):
        code = 4100
        status = False
        message = ''
        result = []

        try:
            token = self.request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                code = 4001
                message = 'Invalid - [ Authorization ]'
                raise Exception(message)

            payload = JWT_DECODE_1(token)
            if payload is None:
                code = 4001
                message = 'Invalid - [ Authorization ]'
                raise Exception(message)

            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            role = payload.get('userRole')

            if role != 'company':
                code = 4004
                message = 'You are not authorized to access this resource'
                raise Exception(message)

            try:
                self.request.body = json.loads(self.request.body)
            except Exception as e:
                code = 4001
                message = 'Request body is not in JSON format'
                raise Exception(message)

            branchId = self.request.body.get('branchId')
            if branchId is None or not isinstance(branchId, str):
                code = 4512
                message = 'Please Enter Valid [ branchId ].'
                raise Exception(message)

            totalEmployeesQ = self.user.aggregate([
                {'$match': {'branchId': ObjectId(branchId)}},
                {'$group': {'_id': None, 'totalEmployees': {'$sum': 1}}},
                {'$project': {'_id': 0, 'totalEmployees': 1}}
            ])
            totalEmployees = next(iter([i async for i in totalEmployeesQ]), {}).get('totalEmployees', 0)

            branchManagerQ = self.user.aggregate([
                {'$match': {'companyId': ObjectId(company_id), 'branchId': ObjectId(branchId)}},
                {'$lookup': {'from': 'role', 'localField': 'role', 'foreignField': '_id', 'as': 'roleData'}},
                {'$unwind': '$roleData'},
                {'$match': {'roleData.role': 'branchManager'}},
                {'$count': 'branchManager'}
            ])
            branchManager = next(iter([i async for i in branchManagerQ]), {}).get('branchManager', 0)

            projectsQ = self.project.aggregate([
                {'$match': {'companyId': ObjectId(company_id), 'branchId': ObjectId(branchId)}},
                {'$group': {
                    '_id': None,
                    'totalProjects': {'$sum': 1},
                    'deliveredProjects': {'$sum': {'$cond': ['$isDelivered', 1, 0]}},
                    'pendingProjects': {'$sum': {'$cond': ['$isDelivered', 0, 1]}}
                }},
                {'$project': {'_id': 0, 'totalProjects': 1, 'deliveredProjects': 1, 'pendingProjects': 1}}
            ])
            projects = next(iter([i async for i in projectsQ]), {})
            totalProjects = projects.get('totalProjects', 0)
            pendingProjects = projects.get('pendingProjects', 0)
            deliveredProjects = projects.get('deliveredProjects', 0)

            totalRolesQ = self.user.aggregate([
                {'$match': {'companyId': ObjectId(company_id), 'branchId': ObjectId(branchId)}},
                {'$lookup': {'from': 'role', 'localField': 'role', 'foreignField': '_id', 'as': 'roleData'}},
                {'$unwind': '$roleData'},
                {'$group': {'_id': '$roleData.role', 'userCount': {'$sum': 1}}},
                {'$project': {'_id': 0, 'role': '$_id', 'userCount': 1}}
            ])
            totalRoles = {role['role']: role['userCount'] for role in await totalRolesQ.to_list(length=None)}

            result = {
                'totalEmployees': totalEmployees,
                'Role Wise Employee': totalRoles,
                'deliveredProjects': deliveredProjects,
                'pendingProjects': pendingProjects,
                'totalProjects': totalProjects,
                'branchManager': branchManager
            }

            status = True
            message = 'Company Details Found'
            code = 200

        except Exception as e:
            if not message:
                template = 'Exception: {0}. Argument: {1!r}'
                code = 5010
                message = 'Internal Error, Please Contact the Support Team.'
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = exc_tb.tb_frame.f_code.co_filename
                Log.w('EXC', template.format(type(e).__name__, e.args))
                Log.d('EX2', f'FILE: {fname} LINE: {exc_tb.tb_lineno} TYPE: {exc_type}')

        response = {
            'code': code,
            'status': status,
            'message': message,
            'result': result
        }
        Log.d('RSP', response)
        try:
            self.write(json.loads(bdumps(response)))
        except Exception as e:
            template = 'Exception: {0}. Argument: {1!r}'
            code = 5011
            message = 'Internal Error, Please Contact the Support Team.'
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = exc_tb.tb_frame.f_code.co_filename
            Log.w('EXC', template.format(type(e).__name__, e.args))
            Log.d('EX2', f'FILE: {fname} LINE: {exc_tb.tb_lineno} TYPE: {exc_type}')
            response = {
                'code': code,
                'status': False,
                'message': message
            }
            self.write(json.loads(bdumps(response)))
        finally:
            await self.finish()
