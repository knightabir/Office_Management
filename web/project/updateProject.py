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

@all_origin
class UpdateProjectHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('OPTIONS', 'PUT')


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
        CONFIG['database'][0]['table'][16]['name']
    ]

    project = MongoMixin.userDb[
        CONFIG['database'][0]['table'][19]['name']
    ]

    def options(self):
        code = 4100
        status = False
        message = ''
        result = []

    async def put(self):
        code = 4100
        status = False
        message = ''
        result = []
        try:
            try:
                token = self.request.headers.get('Authorization')
                if token:
                    token = token.replace('Bearer ', '')
                else:
                    code = 4001
                    message = 'Invalid - [ Authorization ]'
                    status = False
                    raise Exception

                payload = JWT_DECODE_1(token)

                if payload is None:
                    code = 4002
                    message = 'Invalid - [ Authorization ]'
                    status = False
                    raise Exception
            except Exception as e:
                Log.i(e)
                code = 4003
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            # get the user_id company_id and role from the token
            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            role = payload.get('userRole')
            compName = 'project'


            ruleQ = self.user_role_map.aggregate(
                [
                    {
                        '$match': {
                            'user_Id': ObjectId(user_id)
                        }
                    }, {
                        '$lookup': {
                            'from': 'rule', 
                            'localField': 'ruleId.ruleId', 
                            'foreignField': '_id', 
                            'as': 'result'
                        }
                    }, {
                        '$unwind': {
                            'path': '$result', 
                            'preserveNullAndEmptyArrays': True
                        }
                    }, {
                        '$project': {
                            '_id': 0, 
                            'result.name': 1
                        }
                    }
                ]
            )
            if ruleQ is None:
                code = 4003
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception
            rule = []
            async for i in ruleQ:
                rule.append(i['result']['name'])
            if role is None:
                code = 4005
                message = 'you are not authorized user'
                status = False
                raise Exception
            elif compName not in rule:
                code = 4004
                message = 'you are not authorized user'
                status = False
                raise Exception            
            if role not in ('branchManager', 'PROJECTMANAGER'):
                code = 4003
                message = 'You are not authorised to access this resource.'
                raise Exception
            try:
                # Converts the body into json
                self.request.arguments = json.loads(self.request.body)
            except Exception as e:
                code = 4005
                message = 'Expected request Type JSON.'
                raise Exception
            isActive = self.request.arguments.get('isActive')

            if isActive == '' or type(isActive) != bool:
                message = 'isActive is not valid.'
                code = 4512
                raise Exception
            
            projectId = self.request.arguments.get('projectId')
            if projectId is None or not projectId or not isinstance(projectId, str):
                message = 'projectId is not valid.'
                code = 4512
                raise Exception
            
            isDelivered = self.request.arguments.get('isDelivered')
            if isDelivered == '' or type(isDelivered) != bool:
                message = 'isDelivered is not valid.'
                code = 4512
                raise Exception
            

            if isDelivered:
                deleveredOn = timeNow()
            else:
                deleveredOn = None

            # Update the project from the database
            output = await self.project.update_many(
                {
                    '_id': ObjectId(projectId)
                },
                {
                    '$set': {
                        'isActive': isActive,
                        'isDelivered': isDelivered,
                        'deleveredOn': deleveredOn
                    }
                }
            )
            # Check if any documents were updated
            if output.modified_count == 0:
                code = 4513
                message = 'Project not updated.'
                raise Exception(message)
            status = True
            code = 2000
            message = 'Project updated successfully.'
        except Exception as e:
            status = False
            if not len(message):
                template = 'Exception: {0}. Argument: {1!r}'
                code = 5010
                iMessage = template.format(type(e).__name__, e.args)
                message = 'Internal Error, Please Contact the Support Team.'
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = exc_tb.tb_frame.f_code.co_filename
                Log.w('EXC', iMessage)
                Log.d('EX2', 'FILE: ' + str(fname) + ' LINE: ' + str(exc_tb.tb_lineno) + ' TYPE: ' + str(exc_type))
        response = {
            'code': code,
            'status': status,
            'message': message,
            'result': result
        }
        Log.d('RSP', response)
        try:
            self.write(json.loads(bdumps(response)))
            await self.finish()
            return
        except Exception as e:
            status = False
            template = 'Exception: {0}. Argument: {1!r}'
            code = 5011
            iMessage = template.format(type(e).__name__, e.args)
            message = 'Internal Error, Please Contact the Support Team.'
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = exc_tb.tb_frame.f_code.co_filename
            Log.w('EXC', iMessage)
            Log.d('EX2', 'FILE: ' + str(fname) + ' LINE: ' + str(exc_tb.tb_lineno) + ' TYPE: ' + str(exc_type))
            response = {
                'code': code,
                'status': status,
                'message': message
            }
            self.write(json.loads(bdumps(response)))
            await self.finish()