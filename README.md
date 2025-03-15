# nobilis social

create virtualenv

```bash
python -v venv .venv
```


install dependencies
```bash
pip install -r requirements.txt
```



migrations

```bash
python manage.py makemigrations
python manage.py migrate
```



run the app

```bash
python manage.py runserver
```



create superuser

```bash
python manage.py createsuperuser
```


WaitnigList Endpoints
api/v1/waitinglist/  (get, post)
api/v1/waitinglist/<int:pk>/ (get, put, delete)  

Register user
api/v1/register/ post