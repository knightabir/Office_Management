import asyncio
from abc import ABCMeta
import tornado.ioloop
import tornado.web
from build_config import WEB_SERVER_PORT
from util.conn_util import MongoMixin
from util.file_util import FileUtil
from util.log_util import Log

from web.login import LoginHandler
from web.company.addCompany import CompanyCreateHandler
from web.company.addBranch import AddBranchHandler
from web.company.addBranchManager import AddBranchManagerHandler
from web.branchManager.role import RoleHandler
from web.branchManager.payscale import PayScaleHandler
from web.branchManager.addEmployee import AddEmployeeHandler
from web.attendance.attendance import AttendanceHandler
from web.hr.onBoarding import OnBoardingHandler
from web.project.addProject import AddProjectHandler
from web.project.assignProject import ProjectAssignHandler
from web.company.getAllBranch import GetAllBranchHandler
from web.hr.getUser import GetAnyUserHandler
from web.branchManager.dashboard import BranchDashboardHandler
from web.company.companyDashboard import CompanyDashboardHandler
from web.project.updateProject import UpdateProjectHandler
from web.hr.terminateEmploye import TerminateEmployeHandler
from web.branchManager.getUserByRole import GetUserByRoleHandler


class IndexHandler(tornado.web.RequestHandler, metaclass=ABCMeta):
    fu = FileUtil()

    async def prepare(self):
        if not self.request.connection.stream.closed():
            self.set_status(404)
            try:
                with open('./lib/http_error/404.html', 'r') as error_page_file:
                    error_page = error_page_file.read()
                self.write(error_page.format(self.fu.serverUrl))
            except FileNotFoundError:
                self.write("404 Page Not Found")
        await asyncio.sleep(0.001)


class App(tornado.web.Application, MongoMixin):
    def __init__(self):
        settings = {
            'debug': True
        }
        super(App, self).__init__(
            handlers=[
                (r'/', IndexHandler),
                (r'/v1/api/create/company', CompanyCreateHandler),
                (r'/v1/api/login', LoginHandler),
                (r'/v1/api/add/branch', AddBranchHandler),
                (r'/v1/api/add/branch/manager', AddBranchManagerHandler),
                (r'/v1/api/add/employee', AddEmployeeHandler),
                (r'/v1/api/role', RoleHandler),
                (r'/v1/api/onboard', OnBoardingHandler),
                (r'/v1/api/payscale', PayScaleHandler),
                (r'/v1/api/attendance', AttendanceHandler),
                (r'/v1/api/add/project', AddProjectHandler),
                (r'/v1/api/assign/project', ProjectAssignHandler),
                (r'/v1/api/getbranch', GetAllBranchHandler),
                (r'/v1/api/api/get/user', GetAnyUserHandler),
                (r'/v1/api/api/branch/dashboard', BranchDashboardHandler),
                (r'/v1/api/company/dashboard', CompanyDashboardHandler),
                (r'/v1/api/update/project', UpdateProjectHandler),
                (r'/v1/api/terminate/employee', TerminateEmployeHandler),
                (r'/v1/api/user/by/role', GetUserByRoleHandler)
            ],
            **settings,
            default_handler_class=IndexHandler
        )
        Log.i('APP', 'Running Tornado Application Port - [ {} ]'.format(WEB_SERVER_PORT))


if __name__ == "__main__":
    app = App()
    app.listen(WEB_SERVER_PORT)
    tornado.ioloop.IOLoop.current().start()
