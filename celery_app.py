from __init__ import create_app, make_celery

# Create Flask app and Celery instance
flask_app = create_app()
celery = make_celery(flask_app)

# Load Celery configuration
celery.config_from_object('celeryconfig')

# Make Flask app available for tasks
app = flask_app

# Autodiscover tasks
celery.autodiscover_tasks(['tasks'])

if __name__ == '__main__':
    celery.start()