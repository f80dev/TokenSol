Procédure de montage d'un LAMP SSL

1. Générer les certificats et les copiés dans /certs
2. configurer le fichier 000-default.conf avec le répertoire du projet
3. créer l'image via le script built.bat
4. ouvrir les port 443 et 80 du firewall sur le server
5. installer l'image docker
6. remplir le fichier /root/<project_name> avec les fichiers à servir

<pre>
cd /root/temp
curl -s https://api.github.com/repos/PrestaShop/PrestaShop/releases/latest | grep "browser_download_url.*zip" | cut -d : -f 2,3 | tr -d \" | wget -qi -
unzip prestashop_*.zip -d /root/prestashop/
</pre>

7. Lancer l'image via
<pre>
docker rm -f lampserver
docker pull f80hub/lampserver:latest
docker run -d --restart=always -p 8080:80 -p 443:443 --name lampserver -v /root/prestashop:/var/www/html f80hub/lampserver
</pre>

analyser l'image
<pre>
docker run -ti -p 8080:80 -p 443:443 --name lampserver -v /root/prestashop:/var/www/html f80hub/lampserver bash
</pre>




