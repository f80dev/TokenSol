#Installation de PrestaShop

##Installation de la BDD
###Démarrer une instance MariaDB sur un serveur (75.119.159.46 dans l'exemple)

    firewall-cmd --zone=public --add-port=3306/tcp
    docker rm -f mariadb
    docker run -v /root/mariadb:/var/lib/mysql --restart=always -p 3306:3306 --name mariadb -e MARIADB_ROOT_PASSWORD=hh4280 -d mariadb:latest

###démarrer une instance local avec base local

    docker network rm prestashopnet
    docker network create prestashopnet

    docker rm -f MariaDB
    docker volume rm mariadb_volume
    docker volume create mariadb_volume
    docker run --name MariaDB --network prestashopnet --mount source=mariadb_volume,target=/var/lib/mysql --restart=always -p 3306:3306 -e MARIADB_ROOT_PASSWORD=hh4280 -d mariadb:latest

    docker rm -f prestashop
    docker volume rm Prestashop_volume
    docker volume create Prestashop_volume
    docker run --name prestashop --network prestashopnet --add-host host.docker.internal:host-gateway --mount source=Prestashop_volume,target=/var/www/html --restart=always -e DBNAME=nfluent -e PS_FOLDER_INSTALL=install4280 -e PS_ENABLE_SSL=1 -e PS_FOLDER_ADMIN=admin4280 -e DB_SERVER=MariaDB -p 8080:80 -p 4242:4242 -ti prestashop/prestashop


Entrer dans une instance local:

    docker container exec -it prestashop /bin/bash
    docker container exec -it MariaDB /bin/bash

    docker volume inspect Prestashop_volume

Forcer l'usage de TCP
    mysql -u root -phh4280 -h localhost --port 3306 --protocol=tcp



###démarrer une instance local avec base distante
    docker run --name prestashop --mount source=Prestashop_volume,target=/var/www/html --restart=always -e DB_PORT=3306 -e DB_SERVER=75.119.159.46 -p 8080:80 -p 4242:4242 -ti prestashop/prestashop


###Reset local config
    docker network remove prestashopnet
    docker rm -f prestashop
    docker rm -f MariaDB
    docker volume remove mariadb_volume
    docker volume remove Prestashop_volume


##Installation de prestashop (serveur Apache / php)

Documentation: https://hub.docker.com/r/prestashop/prestashop/

###Installation sur le serveur

    firewall-cmd --zone=public --add-port=8080/tcp
    firewall-cmd --zone=public --add-port=4242/tcp
    docker rm -f prestashop
    docker pull prestashop/prestashop
    docker volume rm Prestashop_volume

    docker run --mount source=Prestashop_volume,target=/var/www/html --restart=always --name prestashop -e DBNAME=nfluent -e PS_FOLDER_INSTALL=install4280 -e PS_FOLDER_ADMIN=admin4280 -e DB_SERVER=75.119.159.46 -p 8080:80 -p 4242:4242 -d prestashop/prestashop

il est nécessaire de créer un fichier htaccess : voir https://www.webibazaar.com/blog/how-to-regenerate-htaccess-file-in-prestashop-1-7-x/#:~:text=In%20the%20server%2C%20the%20%E2%80%9C.,displayed%20on%20the%20front%20page.

    cd /root/prestashop
    nano .htaccess
    puis activer les url simplifié depuis la page admin de prestashop



Analyse de l'instance:

    docker container exec -it prestashop /bin/bash

##Configuration finale
###Se connecter dans l'instance prestashop

    docker container exec -it prestashop /bin/bash

Pour la configuration serveur:

  - ouvrir http://161.97.75.165:8080
  - paramétrer la base sur 75.119.159.46 avec root et mot de passe habituel sur la date de naissance d'Emilie


  - Pour la configuration local: changer le nom de la base en prestashop_local (afin de ne pas perturber l'instance distante)

    - Supprimer le répertoire d'installation /root/prestashop/install
    - Renommer le répertoire admin


    rm -f -r install
    mv admin admin4280

Analyser les répertoires : docker exec -it prestashop /bin/bash


Créer la clé d'API avec les permissions suivante:
 - categories
 - customers
 - images
 - products
 - product_features
 - product_feature_values
 - product_suppliers
 - orders
 - stocks_available

