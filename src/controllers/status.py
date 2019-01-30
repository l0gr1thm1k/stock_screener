import connexion
import six

from src import util


def get_healthcheck():  # noqa: E501
    """Healthcheck

    Healthcheck operation used by the load balancer. # noqa: E501


    :rtype: None
    """
    return 'do some magic!'
