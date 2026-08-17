from django.test import SimpleTestCase, override_settings
from core.celery import app
from qa_app.tasks import probe_default_queue_task, probe_ocr_queue_task


class CeleryQueueRoutingTests(SimpleTestCase):
    """
    Isolated test suite for Redis queue routing and Celery task execution.
    https://docs.celeryq.dev/en/stable/userguide/testing.html
    """

    def test_task_routing_queues(self):
        """Verify that tasks are routed to their designated queues (default vs ocr)."""
        default_route = app.amqp.router.route(
            options={},
            name='qa_app.tasks.probe_default_queue_task'
        )
        ocr_route = app.amqp.router.route(
            options={},
            name='qa_app.tasks.probe_ocr_queue_task'
        )

        default_queue_name = default_route['queue'].name if hasattr(default_route.get('queue'),
                                                                    'name') else default_route.get('queue')
        ocr_queue_name = ocr_route['queue'].name if hasattr(ocr_route.get('queue'), 'name') else ocr_route.get('queue')

        self.assertEqual(default_queue_name, 'default')
        self.assertEqual(ocr_queue_name, 'ocr')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_eager_task_execution(self):
        """Verify task execution and return value resolution."""
        res_default = probe_default_queue_task.delay('ping')
        res_ocr = probe_ocr_queue_task.delay('florence_ping')

        self.assertEqual(res_default.get(), 'ping')
        self.assertEqual(res_ocr.get(), 'florence_ping')