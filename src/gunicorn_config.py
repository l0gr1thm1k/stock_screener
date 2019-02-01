import os

from pyhocon import ConfigFactory, ConfigTree, ConfigMissingException


class ApplicationConfig:

    def __init__(self):
        """
        Attempts to determine the application stage and application configuration file
        from system environment variables.  If the variables are undefined, uses default values.
        """
        # determine application stage
        try:
            appStage = os.environ['APPLICATION_STAGE']
        except KeyError:
            appStage = 'LOCAL'

        self.__applicationStage = appStage
        self.__configMap = None

        # determine application configuration filename
        try:
            appConfigFilename = os.environ['APPLICATION_CONFIGURATION_FILENAME']
        except KeyError:
            appConfigFilename = 'application.conf'

        self.__applicationConfigFilename = appConfigFilename
        self.__configMap = {'APPLICATION_CONFIG_FILENAME': self.__applicationConfigFilename}

        # initialize the configuration file
        self.initConfiguration(appStage, appConfigFilename)

    def getApplicationStage(self):

        """
        Retrieve the application stage.

        :return: string with the application stage name
        """

        assert self.__applicationStage
        return self.__applicationStage

    def getConfigMap(self):
        """
        Return the application configuration map.
        :return: Config map with defined configuration.
        """
        return self.__configMap

    def getAppConfigFilename(self):
        """
        Return the filename that was loaded where configuration information was extracted from.
        :return: filename
        """
        assert self.__applicationConfigFilename
        return self.__applicationConfigFilename

    def initConfiguration(self, stage='LOCAL', configFilename='application.conf'):
        """
        Perform initialization.
        :return:
        """

        # define instance variables
        self.__applicationConfigFilename = configFilename
        self.__applicationStage = stage
        self.__configMap = None

        defaultConfig = None
        stageConfig = None
        try:
            # load configuration file
            loadedConfiguration = ConfigFactory.parse_file(self.__applicationConfigFilename)

            # extract default mappings
            try:
                defaultConfig = loadedConfiguration['DEFAULT']
            except ConfigMissingException:
                pass

            try:
                stageConfig = loadedConfiguration[stage]
            except ConfigMissingException:
                pass

            if defaultConfig:
                if stageConfig:
                    self.__configMap = ConfigTree.merge_configs(defaultConfig, stageConfig)
                else:
                    self.__configMap = defaultConfig
            else:
                if stageConfig:
                    self.__configMap = stageConfig
                else:
                    self.__configMap = None
        except IOError:
            pass


CONFIG = ApplicationConfig().getConfigMap()


HOST_PORT = int(os.getenv('HOST_PORT', 8000))
N_WORKERS = int(os.getenv('GUNICORN_WORKERS', 2))
N_THREADS = int(os.getenv('GUNICORN_THREADS', 1))
LOG_LEVEL = CONFIG['logging']['level']
LOG_REQUESTS = CONFIG['logging']['log_requests']
LOG_RESPONSES = CONFIG['logging']['log_responses']


bind = f'0.0.0.0:{HOST_PORT}'
loglevel = 'info'
workers = N_WORKERS
worker_class = 'gthread'
threads = N_THREADS
timeout = 60
graceful_timeout = 30
# Default ELB idle timeout is 60
keepalive = 75
preload_app = True
reload = True
