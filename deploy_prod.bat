cd ./src
copy CNAME_prod CNAME
call ng build --configuration=production --source-map=false --optimization=true --output-hashing=all

cd ..
call gh-pages -d ./docs --repo https://github.com/nfluentdev/tokenforge.git -f -t true -b gh-pages -m "Mise en ligne de production"
echo "Mise en ligne du client terminé"

cd ./src
copy CNAM_prod CNAME

echo "Mise en place du serveur"
cd ../Server
docker build -t f80hub/tokensol .
docker push f80hub/tokensol:latest

cd ..
putty -pw %1 -ssh root@109.205.183.200 -m "install_server_prod.txt"

echo "Traitement terminé"
