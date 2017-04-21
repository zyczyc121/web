from gaggle.settings_dev import *

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # }
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'data_competition_dev',
        'USER': 'dc',
        'PASSWORD': 'dc',
        'HOST': 'biendata.com',
        'PORT': 5432,
    }
}

