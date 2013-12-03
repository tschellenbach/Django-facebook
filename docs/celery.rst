Celery, Performance and Optimization
------------------------------------

Facebook APIs can take quite some time to respond. It's very common that you will wait
between 1-3 seconds for a single API call. If you need multiple calls, pages can quickly become very sluggish.

The recommended solution is to use Celery. Celery is a task queueing system which allows you to
run the API requests outside of the request, response cycle.

Step 1 - Install Celery

Step 2 - Enable Tasks

::

  # use celery for storing friends and likes
  FACEBOOK_CELERY_STORE = True
  # use celery for extending tokens
  FACEBOOK_CELERY_TOKEN_EXTEND = True

When writing your own Facebook functionality you will see a big speedup by using
@facebook_required_lazy
instead of
@facebook_required