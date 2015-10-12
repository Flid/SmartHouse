# -*- coding: utf-8 -*-
from django.views.generic.base import View
import logging
from django.template.response import TemplateResponse
from smart_house.core.exceptions import ValidationFailedError
from django.core.urlresolvers import reverse
from django import http

logger = logging.getLogger('views.base')


class BaseView(View):
    basic_form = None
    auth_actions = None

    def __init__(self):
        super(BaseView, self).__init__()
        self.form_values = {}

    def http_method_not_allowed(self, *args, **kwargs):
        return super(BaseView, self.request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.request = request

        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        return handler(*args, **kwargs)

    def process_basic_form(self, from_form=True):
        logger.info('Processing basic form %s', self.basic_form)

        if self.basic_form is None:
            raise ValueError('No basic_form!')

        args = self.request.POST if from_form else self.request.GET
        logger.debug('Input args: %s', args)

        self.validator = self.basic_form(args)
        if not self.validator.validate():
            raise ValidationFailedError(self.validator.errors)

        self.form_values = self.validator.data

        logger.info('Form has been processed successfully.')


class BaseTemplateView(BaseView):

    def render_to_response(self, template, context=None, **response_kwargs):
        """
        Returns a response, using the `response_class` for this
        view, with a template rendered with the given context.

        If any keyword arguments are provided, they will be
        passed to the constructor of the response class.
        """
        context = context or {}

        return TemplateResponse(
            request=self.request,
            template=template,
            context=context,
            **response_kwargs
        )

    def render_redirect(self, url_name):
        url = reverse(url_name)
        return http.HttpResponseRedirect(url)


class BaseAPIView(BaseView):
    def render_json(self, data):
        return http.JsonResponse(data)
