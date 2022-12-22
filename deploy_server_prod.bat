echo "Mise en place du serveur"
cd ./Server
docker build -t f80hub/tokensol .
docker push f80hub/tokensol:latest

cd ..
putty -pw %1 -ssh root@173.249.41.158 -m "install_server_prod.txt"

echo "Traitement terminé"
