echo "Construction de l'image"
docker image build -t f80hub/lampserver .
docker push f80hub/lampserver
echo "Construction terminée"

echo "ouvrir le firewall avec "
echo "docker run -d --restart=always --rm -p 8080:80 -p 443:443 --name lampserver -v /root/prestashop:/var/www/html f80hub/lampserver"

