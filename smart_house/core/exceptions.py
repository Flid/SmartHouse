# -*- coding: utf-8 -*-
import logging


class SmartHouseBaseError(Exception):
    _code = None
    http_code = 200
    logging_level = logging.INFO
    log_traceback = False

    def render_error(self):
        return {
            'status': 'error',
            'error_code': self._code,
        }


class ValidationFailedError(SmartHouseBaseError):
    """Validation form error"""
    _code = 'args.invalid'

    def __init__(self, errors, *args, **kwargs):
        self._errors = errors
        super(ValidationFailedError, self).__init__(*args, **kwargs)

    def render_error(self):
        data = super(ValidationFailedError, self).render_error()
        data['eror_details'] = self._errors

        return data

class InternalError(SmartHouseBaseError):
    _code = 'internal'
    http_code = 503
    logging_level = logging.CRITICAL
    log_traceback = True


class BadRequestError(SmartHouseBaseError):
    """
    Raise this exception for any error that is too low-level to write something usefull for user,
    but should not be logged as error.
    """
    _code = 'bad_request'


class UserNotFound(SmartHouseBaseError):
    _code = 'user.not_found'


class SocialProfileNotFound(SmartHouseBaseError):
    _code = 'social_profile.not_found'


class PasswordInvalid(SmartHouseBaseError):
    _code = 'user.password_mismatch'


class UserAlreadyExists(SmartHouseBaseError):
    _code = 'user.already_exists'


class UserInactive(SmartHouseBaseError):
    _code = 'user.not_active'


class NotAuthenticated(SmartHouseBaseError):
    _code = 'auth.required'


class GoalNotFound(SmartHouseBaseError):
    _code = 'goal.not_found'


class GoalPermissionDenied(SmartHouseBaseError):
    _code = 'goal.permission_denied'


class NetworkError(SmartHouseBaseError):
    _code = 'network.failed'


class ProviderCommunicationError(SmartHouseBaseError):
    _code = 'social_provider.error'


class UserDeniedError(SmartHouseBaseError):
    _code = 'user.denied'
