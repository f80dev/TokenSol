#Installation de PrestaShop

##Installation de la BDD sur 75.119.159.46
démarrer une instance MariaDB sur un serveur:

    firewall-cmd --zone=public --add-port=3306/tcp
    docker rm -f mariadb
    docker run -v /root/mariadb:/var/lib/mysql --restart=always -p 3306:3306 --name mariadb -e MARIADB_ROOT_PASSWORD=hh4280 -d mariadb:latest


##Installation de prestashop

Documentation: https://hub.docker.com/r/prestashop/prestashop/


    docker rm -f prestashop
    docker run --restart=always --name prestashop -e DB_SERVER=75.119.159.46 -p 8080:80 -d prestashop/prestashop


puis ouvrir http://161.97.75.165:8080 et paramétrer la base sur 75.119.159.46 avec root et mot de passe
habituel sur la date de naissance d'Emilie

Supprimer le répertoire d'installation /root/prestashop/install

rm -f -r install
mv admin admin4280

Analyser les répertoires : docker exec -it prestashop /bin/bash


