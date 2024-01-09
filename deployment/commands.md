```
chown -R root:www-data /root/album_of_the_week
chmod -R 775 /root/album_of_the_week
```

Cron

```
0 0 * * 7 /root/album_of_the_week/deployment/cronjob.sh
```
