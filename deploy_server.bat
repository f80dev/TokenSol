echo "Mise en place du serveur"
cd ./Server
docker build -t f80hub/tokensol .
docker push f80hub/tokensol:latest

cd ..
putty -pw %1 -ssh root@38.242.210.208 -m "install_server.txt"

echo "Traitement terminé"
