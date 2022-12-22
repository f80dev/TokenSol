echo "Mise en place du serveur"
cd ./Server
docker build -t f80hub/tokensol .
docker push f80hub/tokensol:latest

cd ..
putty -pw %1 -ssh root@75.119.159.46 -m "install_server.txt"

echo "Traitement terminé"
