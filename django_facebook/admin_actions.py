from django.contrib import admin
from django.shortcuts import render_to_response
from django.contrib.auth import models as auth_models
from django import template
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)
from django.contrib import messages


def retry_facebook_invite(modeladmin, request, queryset):
    '''
    Retries sending the invite to the users wall
    '''
    invites = list(queryset)
    user_invites = defaultdict(list)
    for invite in invites:
        user_invites[invite.user].append(invite)

    for user, invites in user_invites.items():
        profile = user.get_profile()
        graph = profile.get_offline_graph()
        if not graph:
            error_message = 'couldnt connect to the graph, user access token is %s' % profile.access_token
            messages.error(request, error_message)
            continue
        logger.info('got graph %s for user %s, retrying %s invites',
                    graph, user, len(invites))
        for invite in invites:
            invite_result = invite.resend(graph)
            message = 'User %s sent attempt to sent with id %s s6 is %s' % (
                user, invite_result.wallpost_id, not invite_result.error)
            if invite_result.error:
                message += ' got error %s' % invite_result.error_message
            messages.info(request, message)

        profile.update_invite_denormalizations()
        profile.save()


def retry_open_graph_share(modeladmin, request, queryset):
    for open_graph_share in queryset:
        open_graph_share.retry()
        messages.info(request, 'resent share %s' % open_graph_share.id)


def retry_open_graph_share_for_user(modeladmin, request, queryset):
    from django_facebook import tasks
    users = []
    for share in queryset:
        users.append(share.user)

    users = list(set(users))
    for user in users:
        tasks.retry_open_graph_shares_for_user(user)
