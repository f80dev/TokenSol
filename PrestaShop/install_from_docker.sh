docker network create prestashop-net
# launch mysql 5.7 container
docker run -ti --name mysql --network prestashop-net -e MYSQL_ROOT_PASSWORD=admin -p 3307:3306 -d mysql:5.7
# launch prestashop container, voir https://hub.docker.com/r/prestashop/prestashop

rm -r prestashop && mkdir prestashop
#-v /var/www/html:/root/prestashop \
#-e DB_USER=root \
#        -e DB_NAME=prestashop_db \
#        -e PS_ERASE_DB=1 \
#        -e PS_INSTALL_DB=1 \

docker rm -f nfluent-prestashop
docker run -ti --name nfluent-prestashop --network prestashop-net \
        -e DB_SERVER=mysql:3306 \
        -e PS_FOLDER_ADMIN=admin4280 \
        -e PS_FOLDER_INSTALL=install4280 \
        -e ADMIN_MAIL=herve@nfluent.io -e ADMIN_PASSWD=hh42714280 \
        -p 8080:80 -p 443:443 -d prestashop/prestashop:latest

docker exec -it nfluent-prestashop bash

#La configuration se fait en se connectant sur mysql:3306 comme server en ouvrant
#http://173.249.41.158:8080/install4280

