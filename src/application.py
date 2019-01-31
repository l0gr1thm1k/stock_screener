import connexion
import os

from flask import redirect


HOST_PORT = int(os.getenv('HOST_PORT', 8000))        

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


if __name__ == '__main__':
    application.run(port=HOST_PORT)
