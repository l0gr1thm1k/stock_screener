import connexion
import json



from common.logging import get_new_request_id, log_exception, setup_logging
from copy import deepcopy
from datetime import datetime
from flask import redirect, request, Response
from gunicorn_config import HOST_PORT, LOG_LEVEL, LOG_REQUESTS, LOG_RESPONSES
from structlog import get_logger
from werkzeug.routing import RequestRedirect


# Set up logging
setup_logging(LOG_LEVEL)
logger = get_logger()

logger.info('Loading Stock Screening Service')


# Configure app
application = connexion.FlaskApp(__name__)
application.add_api('./swagger/swagger.yaml')


@application.route('/')
def redirect_to_ui():
    """
    redirects base path to Swagger UI
    :return: redirect
    """

    return redirect("/ui/")


@application.app.before_request
def before_request():
    """
    append UUIDs to all requests and log request
    """

    request.id = get_new_request_id()

    # Get request data
    if request.view_args:
        path_variables = deepcopy(request.view_args)
        # Remove filename key to prevent it from sticking around
        path_variables.pop('filename', None)
    else:
        path_variables = {}
    if request.args:
        query_parameters = request.args.to_dict()
    else:
        query_parameters = {}
    if request.mimetype == 'application/json':
        request_data = request.get_json(silent=True)
    else:
        request_data = {}

    logger = get_logger(requestId=request.id,
                        requestMethod=request.method,
                        requestPath=request.path,
                        remoteIPAddress=request.remote_addr,
                        **path_variables,
                        **query_parameters)

    if LOG_REQUESTS:
        logger.debug('Clustering request', clusteringRequest=str(request_data))

    request.start_time = datetime.now()


@application.app.after_request
def after_request(response):
    """
    log service response

    :param response: Response
    :rtype: Response
    """

    logger = get_logger()

    if response.mimetype == 'application/json':
        response_data = response.get_json(silent=True)
    else:
        response_data = {}

    if LOG_RESPONSES:
        logger.debug('Screening response', statusCode=response.status_code, clusteringResponse=str(response_data))

    return response


@application.app.errorhandler(Exception)
def internal_server_error(ex):
    """
    log all unhandled exceptions

    :param ex: exception
    :return: 500 response
    """

    # Handle redirects
    if isinstance(ex, RequestRedirect):
        return ex
    else:
        log_exception(ex)
        return Response(json.dumps({'message': f'Unhandled exception in Clustering application: {ex}'},
                                   ensure_ascii=False, sort_keys=True), status=500, mimetype='application/json')


if __name__ == '__main__':
    application.run(port=HOST_PORT)
