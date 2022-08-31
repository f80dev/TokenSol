#build : docker build -t f80hub/prestashop_nfluent .
#push : docker push f80hub/prestashop_nfluent
#production: docker run --name prestashop --network prestashopnet --add-host host.docker.internal:host-gateway --mount source=Prestashop_volume,target=/var/www/html --restart=always -e DBNAME=nfluent -e PS_FOLDER_INSTALL=install4280 -e PS_ENABLE_SSL=1 -e PS_FOLDER_ADMIN=admin4280 -e DB_SERVER=MariaDB -p 8080:80 -p 4242:4242 -ti prestashop/prestashop

#
#effacer toutes les images : docker rmi $(docker images -a -q)
#effacer tous les containers : docker rm  $(docker ps -a -f status=exited -q)

#renouvellement des certificats
#désactiver le parefeu puis
#certbot certonly --standalone --email hhoareau@gmail.com -d server.f80lab.com
#cp /etc/letsencrypt/live/server.f80lab.com/* /root/certs


FROM prestashop/prestashop:latest
LABEL maintainer="hhoareau <hhoareau@gmail.com>"

COPY httpd.conf ./etc

RUN a2enmod ssl
RUN chmod 777 -R /var/www/html

