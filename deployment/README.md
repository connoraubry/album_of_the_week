# Installing to a server

[Guide Link](https://developers.redhat.com/articles/2023/08/17/how-deploy-flask-application-python-gunicorn#the_application)

[Guide 2](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04)

The guide assumes the repo is cloned to /root/

All commands are run from the `album_of_the_week` directory

1. Install requirements

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. (OPTIONAL?) Change permissions

```
chown -R root:www-data /root/album_of_the_week
chmod -R 775 /root/album_of_the_week
```

3. Set up website service

```
cp deployment/aotw.service /etc/systemd/system/
sudo systemctl start aotw
sudo systemctl enable aotw
```

4. Set up cronjob for weekly updates

```
0 0 * * 7 /root/album_of_the_week/deployment/cronjob.sh
```

5. Copy nginx config

```
cp /root/album_of_the_week/deployment/aotw.nginx /etc/nginx/sites-available/aotw
ln -s /etc/nginx/sites-available/aotw /etc/nginx/sites-enabled/aotw
```

6. Test nginx config, reset nginx if good

```
nginx -t
systemctl restart nginx
```

7. Configure API keys

Create a file called `.env` in `album_of_the_week/` directory.
Add your last.fm api key and secret.
```
LASTFM_API_KEY="1234567890abcdef"
LASTFM_API_SECRET="1234567890abcdef"
```
