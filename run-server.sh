
if [ -z $1 ]; 
  then
    echo 'Usage: run-server.sh <env_name>'
    exit 1
fi

./ve/bin/python manage.py runserver 127.0.0.1:8090 --settings=smart_house.settings.$1
