import connexion
import os

HOST_PORT = int(os.getenv('HOST_PORT', 8000))


# Configure app
application = connexion.FlaskApp(__name__)
application.add_api('./swagger/swagger.yaml')


if __name__ == '__main__':
    application.run(port=HOST_PORT)
