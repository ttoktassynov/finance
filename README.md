# finance

This is simple web application that can get quote for different stocks from iexcloud.io website. It also allows you to buy, sell, see history of transactions in your profile.

The app is servied via `waitress` and run on `flask` framework with `sqlite3` database on the backend and `Jinja` templates on the front-end.

The app can be viewed on [Heroku](http://stocktrading21.herokuapp.com/)

## Configuration

- Visit [iexcloud](iexcloud.io/cloud-login#/register/) and obtain token
- Prepare environmental variables. For local development install `pip install python-decouple`, create `.env` file, to which include `API_KEY=your_token`. For producation deployment include that key value pair in settings.

## Run

- Run `python application.py`

## Run with Docker locally

- Run `docker build --tag finance .` to build an image
- Run `docker run -p 5000:5000 finance` to run the container

## Deployment on Heroku

- Create `heroku.yml` manifest:

```[yml]
build:
  docker:
    web: Dockerfile
```

- Commit changes to heroku git:

```[git]
git add heroku.yml
git commit -m "Add heroku.yml"
```

- Set the stack of your app to container:
`heroku stack:set container`

- Push your app to Heroku
`git push heroku master`
